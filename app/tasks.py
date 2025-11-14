# /scripts/cluster_script.py
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np
import os
import sys

# (关键) 将项目根目录添加到 Python 路径中

from . import  db
from .models import Restaurant, UserBehaviorLog, UserPriceLevel



def run_ml_pipeline():
    """
    执行 "Per-Merchant" (逐个商家) 聚类管道
    """
    print("Starting ML Pipeline (Per-Merchant Logic)...")
    
    
        
        # --- 1. 清空所有旧的 PriceLevel 数据 ---
        #    我们将在循环外一次性清空，并在最后统一提交
    try:
        UserPriceLevel.query.delete()
        print("Cleared old UserPriceLevel data.")
    except Exception as e:
            #db.session.rollback()
        print(f"Error clearing old data: {e}")
        return

        # --- 2. 获取所有餐厅 ---
    all_restaurants = Restaurant.query.all()
    if not all_restaurants:
        print("No restaurants found. Exiting.")
        return

    print(f"Found {len(all_restaurants)} restaurants to process.")
        
        # 准备一个列表，收集所有的新 PriceLevel 条目
    all_new_levels = []

        # --- 3. (核心逻辑) 遍历每一家餐厅 ---
    for restaurant in all_restaurants:
        print(f"\n--- Processing Restaurant ID: {restaurant.RestaurantID} ({restaurant.Name}) ---")
            
            # 3.1. (Input) 只查询这家餐厅的行为日志
        query = db.session.query(
            UserBehaviorLog.UserID, 
            UserBehaviorLog.ActionType
        ).filter(UserBehaviorLog.RestaurantID == restaurant.RestaurantID)
            
        df_logs = pd.read_sql(query.statement, db.engine)

        if df_logs.empty:
            print("No behavior logs found for this restaurant. Skipping.")
            continue
                
        print(f"Loaded {len(df_logs)} behavior logs.")

            # 3.2. (Feature Engineering) 为这家餐厅构建特征
            #    注意：index 现在只是 UserID，因为 RestaurantID 是固定的
        try:
            df_features = pd.pivot_table(
                df_logs,
                index=['UserID'], # 索引只是用户
                columns='ActionType',
                aggfunc=len,
                fill_value=0
            )
        except Exception as e:
            print(f"Error during pivot_table: {e}. Skipping restaurant.")
            continue

        print("Feature engineering complete. Feature matrix:")
        print(df_features)
            
            # 3.3. (数据检查) 确定聚类数量
        n_users = len(df_features)
            
            # 我们的目标是 5 个 Level，但如果用户数少于 5，我们就只能聚成 n_users 个簇
        n_clusters = min(n_users, 5) 
            
        if n_clusters <= 1:
            print(f"Only {n_users} user(s). Clustering not meaningful. Skipping.")
                # (可选：可以给这1个用户一个默认等级，但我们暂时跳过)
            continue
                
        print(f"Clustering {n_users} users into {n_clusters} levels...")

            # 3.4. (Scaling) 标准化
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(df_features)

            # 3.5. (K-Means) 运行聚类
        kmeans = KMeans(
                n_clusters=n_clusters, 
                random_state=42, 
                n_init=10
        )
        df_features['cluster_raw'] = kmeans.fit_predict(features_scaled)

            # 3.6. (Rank & Map) 映射聚类到 PriceLevel (1-5)
        centers = kmeans.cluster_centers_
        cluster_value = centers.sum(axis=1) # 计算每个簇的“总价值”
        cluster_ranking = np.argsort(cluster_value) # 排序

        levels = np.round(np.linspace(1, 5, n_clusters)).astype(int)
            
            # { 原始聚类ID: 映射后的 PriceLevel }
        level_map = {cluster_id: levels[rank] for rank, cluster_id in enumerate(cluster_ranking)}
            
        df_features['PriceLevel'] = df_features['cluster_raw'].map(level_map)

        print("Mapped clusters to PriceLevel:")
        print(f"Raw clusters: {np.unique(df_features['cluster_raw'])}")
        print(f"Level map: {level_map}")

            # 3.7. (Collect) 收集结果
        df_output = df_features.reset_index()
        for _, row in df_output.iterrows():
            new_level_entry = UserPriceLevel(
                UserID=int(row['UserID']),
                RestaurantID=restaurant.RestaurantID, # 关键：使用当前循环的餐厅ID
                PriceLevel=int(row['PriceLevel'])
            )
            all_new_levels.append(new_level_entry)
            
        print(f"Processed {len(df_output)} users for this restaurant.")
        
        # --- 4. (Output) 统一写入数据库 ---
        total_updated = 0
        if all_new_levels:
            try:
                db.session.add_all(all_new_levels)
                db.session.commit()
                total_updated = len(all_new_levels)
                print(f"\n--- ML Pipeline Complete! ---")
                print(f"Successfully updated/inserted {total_updated} entries.")
            except Exception as e:
                db.session.rollback()
                print(f"\nError committing new levels to DB: {e}")
                return {"error": f"DB commit error: {str(e)}", "success": False}
        else:
            print("\n--- ML Pipeline Complete! ---")
            print("No new price levels were generated.")
            
        # (新) 返回一个成功的结果字典
        return {"success": True, "message": f"K-Means 运行完毕！成功更新 {total_updated} 条用户等级。"}

if __name__ == '__main__':
    run_ml_pipeline()