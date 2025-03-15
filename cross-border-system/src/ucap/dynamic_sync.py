from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from .graph_builder import KnowledgeGraph

class DataWatcher(FileSystemEventHandler):
    def __init__(self):
        self.kg = KnowledgeGraph()
    
    def on_modified(self, event):
        if event.src_path.endswith("risk_data.csv"):
            print("\n🔄 检测到数据变化，触发图谱更新...")
            self.kg.build_graph("src/data/risk_data.csv")
            print("✅ 知识图谱已更新")

def start_monitoring():
    observer = Observer()
    observer.schedule(DataWatcher(), path="src/data")
    observer.start()
    print("👀 启动监控：正在监听 data/ 目录变化...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_monitoring()
