import subprocess
import sys

def install_modules():
    modules = ["fastapi", "uvicorn[standard]"]

    for module in modules:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])
            print(f"成功安裝/檢查: {module}")
        except Exception as e:
            print(f"安裝 {module} 失敗: {e}")

if __name__ == "__main__":
    install_modules()
    print("\n環境準備就緒")