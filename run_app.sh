#!/bin/bash

# Streamlit 앱 실행 스크립트
echo "이미지 평가 결과 검수 시스템을 시작합니다..."

# 필요한 패키지 설치
echo "필요한 패키지를 설치합니다..."
pip install -r requirements.txt

# Streamlit 앱 실행
echo "Streamlit 앱을 실행합니다..."
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 