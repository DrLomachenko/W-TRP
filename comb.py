#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

# 1. Merging CSV files (from merge.py)
def merge_csv_files():
    results_folder = 'results'
    merged_data = None
    
    # Iterate through all files in the 'results' folder
    for filename in os.listdir(results_folder):
        if filename.startswith('result') and filename.endswith('.csv'):
            file_path = os.path.join(results_folder, filename)
            data = pd.read_csv(file_path)
            
            # Merge based on the 'test' column (inner join)
            if merged_data is None:
                merged_data = data
            else:
                merged_data = pd.merge(merged_data, data, on='test', how='inner')
    
    # Renaming columns for each algorithm
    for col in merged_data.columns:
        if col.startswith('total_cost'):
            algo = col.replace('total_cost', '')
            merged_data.rename(columns={col: f'total_cost_{algo}'}, inplace=True)
        elif col.startswith('millis'):
            algo = col.replace('millis', '')
            merged_data.rename(columns={col: f'millis_{algo}'}, inplace=True)
    
    # Save the merged data to a new CSV
    merged_data.to_csv('results/combined_results.csv', index=False)
    return merged_data

# 2. Plotting data (from plot.py)
def plot_data():
    file_path = 'results/combined_results.csv'
    data = pd.read_csv(file_path)
    
    # Identify all algorithms
    algorithms = [col for col in data.columns if col.startswith('millis_')]
    algorithm_names = [algorithm.replace('millis_', '') for algorithm in algorithms]

    # Calculate the average time for each algorithm
    average_times = data[algorithms].mean()

    # Plotting
    plt.figure(figsize=(10, 6))
    colors = cm.get_cmap('tab10', len(algorithms))

    for i, algorithm in enumerate(algorithms):
        plt.plot(data['test'], data[algorithm], label=algorithm_names[i], color=colors(i))

    plt.xlabel('Test')
    plt.ylabel('Millis')
    plt.title('Comparison of Algorithms')
    plt.legend()
    plt.show()

# Main function to execute both merge and plot
def main():
    # Step 1: Merge CSV files
    merged_data = merge_csv_files()
    
    # Step 2: Plot data
    plot_data()

if __name__ == "__main__":
    main()
