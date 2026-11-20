#Starts from python 3.11-slim
FROM python:3.11-slim

#sets environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NLTK_DATA=/opt/nltk_data

WORKDIR /app

# libgomp is required by faiss-cpu and PyTorch on Debian-based images.
RUN apt-get update \
    && apt-get install --no-install-recommends -y libgomp1 \
    && rm -rf /var/lib/apt/lists/*

#copies requirement.txt and installs python packages
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    # downloads punkt tokeniser during the image build, so pdf processing doesnt need to download it at runtime
    && python -m nltk.downloader -d "$NLTK_DATA" punkt

#copies the backend code into /app
COPY . ./

EXPOSE 8000

# starts fastapi
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
