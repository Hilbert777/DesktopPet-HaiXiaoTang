import os
import requests
import sys

# 模型下载地址 (Qwen1.5-0.5B-Chat-GGUF, tiny and fast)
MODEL_URL = "https://hf-mirror.com/Qwen/Qwen1.5-0.5B-Chat-GGUF/resolve/main/qwen1_5-0_5b-chat-q4_k_m.gguf"
MODEL_DIR = "modle" # Note: User's folder is named 'modle' based on workspace into
MODEL_FILENAME = "qwen1_5-0_5b-chat-q4_k_m.gguf"

def download_file(url, dest_path):
    print(f"Downloading model from {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        sys.stdout.write(f"\rProgress: {percent:.2f}%")
                        sys.stdout.flush()
        print("\nDownload complete!")
        return True
    except Exception as e:
        print(f"\nDownload failed: {e}")
        return False

def main():
    # 确定项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(project_root, MODEL_DIR)
    
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        
    dest_path = os.path.join(model_dir, MODEL_FILENAME)
    
    if os.path.exists(dest_path):
        print(f"Model already exists at {dest_path}")
        return

    print("Desktop Pet requires a GGUF model to chat.")
    print("Attempting to download Qwen1.5-0.5B (approx 400MB)...")
    
    if download_file(MODEL_URL, dest_path):
        print(f"Model saved to {dest_path}")
        print("Please ensure your config.json points to this file.")
        
        # update config if exists
        config_path = os.path.join(model_dir, "config.json")
        if os.path.exists(config_path):
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # Update path to be relative to project root or absolute
            # config["model_path"] = f"modle/{MODEL_FILENAME}" 
            # actually better to use relative path for portability
            pass

if __name__ == "__main__":
    main()
