import streamlit as st
import openai
from pinecone import Pinecone

class RAGChatbot:
    def __init__(self):
        # 1. Initialize OpenAI
        self.openai_api_key = st.secrets["OPENAI_API_KEY"]
        self.client = openai.OpenAI(api_key=self.openai_api_key)

        # 2. Initialize Pinecone with Namespace
        try:
            self.pc = Pinecone(api_key=st.secrets["pinecone"]["api_key"])
            self.index_name = st.secrets["pinecone"]["index_name"]
            # Add namespace support if you use it (check your secrets.toml)
            self.namespace = st.secrets["pinecone"].get("namespace", "default") 
            self.index = self.pc.Index(self.index_name)
            self.is_connected = True
            print(f"✅ [SYSTEM] Connected to Pinecone Index: {self.index_name} (Namespace: {self.namespace})")
        except Exception as e:
            print(f"❌ [ERROR] Pinecone Connection Failed: {e}")
            self.is_connected = False

    def _get_embedding(self, text):
        """Generates embedding for the query."""
        try:
            response = self.client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ [ERROR] Embedding Failed: {e}")
            return None

    def _retrieve_context(self, query):
        """Queries Pinecone for relevant PDF chunks."""
        if not self.is_connected:
            return None

        print(f"🔍 [RAG] Generating embedding for: '{query}'")
        vector = self._get_embedding(query)
        if not vector:
            return None

        try:
            print(f"🔍 [RAG] Querying Pinecone...")
            results = self.index.query(
                vector=vector,
                top_k=3,
                include_metadata=True,
                namespace=self.namespace # <--- Critical: Use your namespace
            )
            
            # Extract text
            contexts = [match['metadata']['text'] for match in results['matches'] if 'text' in match['metadata']]
            
            # VERBOSE LOGGING IN TERMINAL
            if contexts:
                print(f"✅ [RAG] Found {len(contexts)} relevant chunks.")
                for i, ctx in enumerate(contexts):
                    print(f"   --- Chunk {i+1} ---\n   {ctx[:100]}...\n")
            else:
                print("⚠️ [RAG] No relevant context found.")
                
            return "\n\n".join(contexts)
        except Exception as e:
            print(f"❌ [ERROR] Retrieval Failed: {e}")
            return None

    def get_response(self, user_input, chat_history):
        """
        Main function. Returns ONLY the response text.
        Debug info is printed to the terminal.
        """
        # 1. Get Context
        context_text = self._retrieve_context(user_input)
        
        # 2. Build the System Prompt
        system_prompt = f"""
        ### The Jamie Date Persona
        You are Jamie Date, a celebrated dating coach for men. 
        Style: Punchy, casual, texting a friend. Use emojis naturally. No markdown lists.
        
        ### KNOWLEDGE BASE (Strategies from your library):
        {context_text if context_text else "No specific playbook strategy found. Use general expert knowledge."}
        
        ### Current Context:
        Respond to the user as Jamie. Keep it under 250 words.
        """

        # 3. Construct Message History
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history[-6:]) 
        messages.append({"role": "user", "content": user_input})

        # 4. Generate Response
        print("🤖 [LLM] Generating response...")
        try:
            completion = self.client.chat.completions.create(
                model="ft:gpt-4o-mini-2024-07-18:jamie-date:jamiegpt-data-humanchat-custom:CIgpsCAk", 
                messages=messages,
                temperature=0.7
            )
            response = completion.choices[0].message.content
            print(f"✅ [LLM] Response generated: {len(response)} chars.")
            return response
        except Exception as e:
            print(f"❌ [ERROR] LLM Generation Failed: {e}")
            return "My signal is breaking up. Try again?"

# Singleton Instance
coach_bot = RAGChatbot()