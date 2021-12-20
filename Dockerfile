FROM tadeorubio/pyodbc-msodbcsql17
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
# RUN mkdir ~/.streamlit
# RUN cp config.toml ~/.streamlit/config.toml
# RUN cp credentials.toml ~/.streamlit/credentials.toml
# ENV PORT 80
EXPOSE 8501
ENTRYPOINT ["streamlit", "run"]
CMD ["app.py"]
