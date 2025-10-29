# Python 3.13으로 환경 재생성
  conda deactivate
  conda env remove -n edumentor -y
  conda create -n edumentor python=3.13 -y
  conda activate edumentor

  # 설치
  pip install --upgrade pip
  pip install -r requirements.txt