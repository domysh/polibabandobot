# Usa un'immagine base Python ufficiale
FROM python:3.13

# Imposta la directory di lavoro all'interno del container
WORKDIR /app

# Copia il file requirements.txt e installa le dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutti i file del bot nella directory di lavoro
COPY . .

CMD ["python", "bot.py"]
