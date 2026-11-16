import os
from langchain_openai import ChatOpenAI , OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

def create_vector_store(resumes):

    documents = []

    for resume in resumes:

        document = Document(

            page_content= resume["text"],
            metadata = {
                "candidate": resume["name"],
                "file": resume["file"]
            }
        )

        documents.append(document)

    splitter = RecursiveCharacterTextSplitter(

        chunk_size = 400 ,
        chunk_overlap = 100 
    )

    chunks = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings(

        model= "text-embedding-3-small"

    )

    vector_store = FAISS.from_documents( chunks , embeddings )

    return vector_store


def ask_rag( vector_store , query ) :

    retriever = vector_store.as_retriever(
        search_kwargs = { "k": 5 }
    )

    retrieved_docs = retriever.invoke(query)

    context = "\n\n".join(

        [
           f"Candidate: {doc.metadata['candidate']}\n"
           f"Resume Content:\n{doc.page_content}"
           for doc in retrieved_docs

        ]
    )


    prompt = ChatPromptTemplate.from_messages(
        [
            (

                "system",

                """
You are a Resume Screening Assistant.

Answer questions only using the provided resume context.

If the requested information is not present,
say that it was not found in the resumes.

For candidate-related questions:
- mention candidate names
- mention relevant skills
- do not invent experience
- keep the answer concise

Resume Context:
{context}

"""
            ),
            (
                "human",
                "{query}"
            )
        ]
    )

    llm = ChatOpenAI(

        model= "gpt-4o-mini",
        temperature= 0

    )

    chain = prompt | llm

    response = chain.invoke(
        {

            "context" : context ,
            "query" : query 
        }
    )

    return response.content , retrieved_docs

