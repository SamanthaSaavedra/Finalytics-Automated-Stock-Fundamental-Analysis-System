# Finalytics

[![EN](https://img.shields.io/badge/EN-English-blue?style=for-the-badge)](https://github.com/SamanthaSaavedra/Finalytics-Automated-Stock-Fundamental-Analysis-System/blob/main/README.MD)
[![ES](https://img.shields.io/badge/ES-Español-red?style=for-the-badge)](https://github.com/SamanthaSaavedra/Finalytics-Automated-Stock-Fundamental-Analysis-System/blob/main/README.ES.MD)

<p align="justify"> 
En la actualidad la <b>cantidad de conocimiento e inferencia necesaria para entender la inversión ha aumentado drásticamente</b>, cuando se trata de opciones para abordar la gestión patrimonial el <b>mercado de valores</b> podría ser una de las múltiples alternativas, sin embargo, la frontera del conocimiento es alta y el tiempo disponible insuficiente. 
</p>

<p align="justify">
Finalytics es un <b>analizador financiero para empresas estadounidenses que cotizan en bolsa</b>, capaz de sintetizar los últimos cinco años de reportes anuales en un resumen conciso con gráficas y una explicación corta en lenguaje natural. El sistema utiliza un <b>Large Language Model (LLM)</b> contextualizado con <b>Retrieval-Augmented Generation (RAG)</b> para reducir alucinaciones y proporcionar respuestas más precisas y útiles.
</p>

<p align="justify"> 
Integra una <b>arquitectura de software Modelo Controlador Vista (MCV) con Docker</b> usando principios de microservicios para aislar cada componente en un contenedor distinto y brindar mayor escalabilidad para más usuarios en plataformas en la nube.
</p>

<p align="justify">
Cada contenedor posee <b>políticas de QoS</b> donde Docker Compose intenta, dentro de un tiempo determinado (menos de 60 segundos), realizar una consulta de salud para verificar que el contenedor esté activo. Cuando se agotan los intentos, se derriba el Process ID (PID) y Docker vuelve a desplegar el contenedor.
</p>

https://github.com/user-attachments/assets/62b2f332-8657-4506-8f25-375e03962ee0

## Arquitectura Software (MCV)

<p align="justify"> 
La arquitectura propuesta para abordar el problema utiliza MCV (Modelo Controlador Vista), en la cual se siguen las siguientes reglas:
</p>

- **Modelo:** Procesa la lógica del negocio y la aplicación.
- **Controlador:** Comunica la vista y el modelo, gestiona la entrada y actualiza la vista y el modelo.
- **Vista:** Muestra la información proveniente del modelo.

## Docker Segmentación (Microservicios)

<p align="justify">
Docker ayuda a crear entornos virtuales aislados para evitar problemas de dependencias, mejorar la calidad de vida en el desarrollo de software y enriquecer los servicios con políticas de calidad de servicio. El programa propuesto fue dividido siguiendo arquitectura de microservicios, donde cada servicio tiene su propio entorno; así, los cambios y el mantenimiento afectan únicamente al servicio particular y no a todo el producto. 
</p>

<p align="justify">
Utilizando la arquitectura MCV, los contenedores se dividieron de la siguiente manera:
</p>

- **Model:** Sistema RAG y embeddings (Hugging Face y Deepseek).
- **Controller:** Base de datos (MongoDB).
- **View:** Flet.

> [!NOTE]
> La comunicación entre contenedores se realiza usando FastAPI y una red bridge de Docker, lo que significa que se ejecuta localmente y Docker integra un DNS para resolver solicitudes IP. La coordinación entre contenedores es lograda por Docker Compose.

## Workflow

<p align="justify">  
Finalytics trabaja en los siguientes pasos:
</p>

- $${\color{orange} 1.-}$$ Consulta y extrae información desde SEC-API (Sección 7 del 10-K) y Alpha Vantage.
- $${\color{orange} 2.-}$$ La información se almacena en memoria caché para evitar un uso excesivo de consultas, guardándose en una base de datos local MongoDB.
- $${\color{orange} 3.-}$$ Se realiza la extracción de características y luego se envían a Retrieval-Augmented Generation Deepseek con un prompt automático para obtener la mejor respuesta sin comprometer eficiencia.
  - $${\color{lightskyblue} 3.1.-}$$ Divide el texto en fragmentos manejables para evitar colapsos de memoria, concepto similar al batch size en frameworks de inteligencia artificial.
  - $${\color{lightskyblue} 3.2.-}$$ Cada embedding representa un número que se almacena en FAISS.
  - $${\color{lightskyblue} 3.3.-}$$ La respuesta se obtiene con los números más cercanos que coinciden en FAISS.
- $${\color{orange} 4.-}$$ Los contenedores se comunican entre sí para obtener su información y finalmente mostrarla en el contenedor de vista correspondiente.
  - $${\color{lightskyblue} 4.1.-}$$ Cada 60 segundos, como segundo proceso, los contenedores realizan un health check usando su dirección de loopback (127.0.0.1 para IPv4, ::1 para IPv6) para intentar hacer ping varias veces, si no es posible, anula el proceso PID 1 y Docker Compose vuelve a desplegar el contenedor, notificando su estado de salud.

## Video

https://github.com/user-attachments/assets/39b92c00-cb9d-4605-be71-17f56c594d09

> [!CAUTION]
> La versión actual no incluye las API Keys para realizar consultas a la base de datos local y a SEC-api.