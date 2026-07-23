# run_all.py (프로젝트 최상단)
import subprocess
import time

if __name__ == '__main__':
    print("🚀 백엔드와 프론트엔드를 동시에 시작합니다...")
    
    # 1. FastAPI 서버 백그라운드 실행
    backend = subprocess.Popen(["uvicorn", "main:app", "--port", "8000"], cwd="back")
    
    # 서버가 켜질 시간을 4초 기다려줌
    time.sleep(4)
    
    # 2. Streamlit 앱 실행
    frontend = subprocess.Popen(["streamlit", "run", "main.py", "--server.port", "8501"], cwd="front")

    try:
        # 터미널 창이 꺼지지 않도록 대기
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        # Ctrl+C 누르면 둘 다 깔끔하게 종료
        print("🛑 서버를 종료합니다...")
        backend.terminate()
        frontend.terminate()