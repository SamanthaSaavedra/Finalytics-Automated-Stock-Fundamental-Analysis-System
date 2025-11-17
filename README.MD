# Finalytics

[![EN](https://img.shields.io/badge/EN-English-blue?style=for-the-badge)](https://github.com/SamanthaSaavedra/Finalytics-Automated-Stock-Fundamental-Analysis-System/blob/main/README.MD)
[![ES](https://img.shields.io/badge/ES-Español-red?style=for-the-badge)](https://github.com/SamanthaSaavedra/Finalytics-Automated-Stock-Fundamental-Analysis-System/blob/main/README.ES.MD)

<p align="justify">    
Nowadays the <b>amount of knowledge and inference needed to understand investment has drastically increased</b>, when dealing with options to address heritage management the <b>stock market</b> could be one of multiple options to rely on, however the knowledge frontier is high and the amount of time unreachable.
</p>

<p align="justify">    
Finalytics is a <b>financial analyzer for U.S. stock companies</b> that synthesizes the last five years of annual reports into a concise summary with plots and a short natural-language explanation. The system uses a <b>Large Language Model (LLM)</b> contextualized with <b>Retrieval-Augmented Generation (RAG)</b> to reduce hallucinations and provide more accurate and helpful responses.
</p>

<p align="justify">  
Integrates <b>Model Controller View software architecture (MCV) with Docker</b> using the principles of microservices to isolate each component in a different container to provide more scalability for more users using cloud platforms.
</p>

<p align="justify"> 
Each container has <b>QoS policies</b> in which Docker Compose tries within a certain time (less than 60 seconds) a health query to check if the container is up. When the number of tries runs out, the Process ID (PID) is taken down and Docker itself redeploys the container again.
</p>

https://github.com/user-attachments/assets/62b2f332-8657-4506-8f25-375e03962ee0

## Software Architecture (MCV)

<p align="justify">   
The proposed architecture to intend the problem was using MCV (Model Control View) architecture in which they follow the next rules:
</p>

- **Model:** Process the business logic and application.
- **Controller:** Communicates the view and the controller, manages the input and updates the view and model.
- **View:** Display the data from the model.

## Docker Segmentation (Microservices)

<p align="justify">   
Docker helps to create isolated virtual environments to prevent problem dependencies, easier quality of life at software development and enrich the services with quality of service policies, the proposed program was divided according microservices architecture, which every single service has its own environment, thus making changes and maintenance only affects the single service and not the whole product.
</p>

<p align="justify">  
Using the MCV architecture the containers were divided in the next approach:
</p>

- **Model:** RAG and embed system (Hugging Face and Deepseek).
- **Controller:** Database (MongoDB).
- **View:** Flet.

> [!NOTE]
> The communication between containers is done using FastAPI and in a Docker bridge communication network this means is done locally and Docker itself integrates a DNS to solve the IP requests, the coordination between containers is archive by docker compose.

## Workflow

<p align="justify">  
Finalytics works in the following steps:
</p>

- $${\color{orange} 1.-}$$ Queries and extracts the information from SEC-API (Section 7 of 10-K) Alpha Vantage.
- $${\color{orange} 2.-}$$ Information is allocated in cache memory to avoid more query usage at a local MongoDB database.
- $${\color{orange} 3.-}$$ Feature extraction is done and then sent to Retrieval-Augmented Generation Deepseek with an automatic prompt to give the best answer without compromising efficiency.
  - $${\color{lightskyblue} 3.1.-}$$ Divides the text into affordable chunks to avoid collapsing memory, similar concept to batch size in artificial intelligence frameworks.
  - $${\color{lightskyblue} 3.2.-}$$ Each embedding represents a number that is stored in FAISS.
  - $${\color{lightskyblue} 3.3.-}$$ The response is given by the closest numbers that match with the FAISS.
- $${\color{orange} 4.-}$$ The containers communicate with each other to bring their information and finally display it at the entrypoint container view.
  - $${\color{lightskyblue} 4.1.-}$$ Containers every 60 seconds as a second process will do a health check using their loopback address (127.0.0.1 for IPv4, ::1 for IPv6) to try to ping themselves several times; if it is not possible, it takes down the process ID (PID) 1 and Docker Compose redeploys the container, notifying their health state.

## Video

https://github.com/user-attachments/assets/39b92c00-cb9d-4605-be71-17f56c594d09

> [!CAUTION]
> The current version does not include the API Keys to make the query to the local and SEC-api database.
