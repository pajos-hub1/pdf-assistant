from langchain_ollama import ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnablePassthrough
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

# In-memory session store
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

SYSTEM_PROMPT = """
You are a helpful document assistant.
Use the context below to answer the question as thoroughly as possible.
If the answer is partially in the context, use what is available and indicate if more detail is not in the document.
Only say "I don't have enough information in this document" if there is absolutely nothing relevant in the context.

Context:
{context}
"""

def build_qa_chain(vector_store: FAISS):
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    llm = ChatOllama(
        model="llama3.2",
        temperature=0
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])

    def retrieve_and_format(inputs):
        question = inputs["question"]
        docs = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in docs])
        sources = sorted(set([doc.metadata.get("page", "unknown") for doc in docs]))
        return {
            "context": context,
            "question": question,
            "sources": sources
        }

    chain = (
        RunnablePassthrough.assign(
            context=lambda x: retrieve_and_format(x)["context"],
            sources=lambda x: retrieve_and_format(x)["sources"]
        )
        | prompt
        | llm
        | StrOutputParser()
    )

    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="chat_history",
    )

    return chain_with_history, retriever