import os
import streamlit as st
from mem0 import MemoryClient
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ------------------ Streamlit Config ------------------
st.set_page_config(page_title="🧠 Personal Memory App", page_icon="🤖", layout="wide")
st.title("🧠 Personal Memory Manager")
st.markdown("#### Powered by Mem0")

# ------------------ Sidebar: API Keys ------------------
with st.sidebar:
    # === BRANDING SECTION ===
    st.markdown(
        "<div style='text-align: center; margin: 2px 0;'>"
        "<a href='https://www.buildfastwithai.com/' target='_blank' style='text-decoration: none;'>"
        "<div style='border: 2px solid #e0e0e0; border-radius: 6px; padding: 4px; "
        "background: linear-gradient(145deg, #ffffff, #f5f5f5); "
        "box-shadow: 0 2px 6px rgba(0,0,0,0.1); "
        "transition: all 0.3s ease; display: inline-block; width: 100%;'>"
        "<img src='https://github.com/Shubhwithai/chat-with-qwen/blob/main/company_logo.png?raw=true' "
        "style='width: 100%; max-width: 100%; height: auto; border-radius: 8px; display: block;' "
        "alt='Build Fast with AI Logo'>"
        "</div>"
        "</a>"
    "</div>",
    unsafe_allow_html=True
)
    
# Sample memories for demo users
SAMPLE_MEMORIES = {
    "shubham": [
        "I love working on AI projects and machine learning models",
        "My favorite programming languages are Python and JavaScript",
        "I enjoy building web applications with Streamlit",
        "I'm interested in natural language processing and computer vision"
    ],
    "aaryan": [
        "I'm passionate about data science and analytics",
        "I prefer using React for frontend development",
        "My favorite cuisine is Italian food",
        "I enjoy playing cricket on weekends"
    ],
    "prathmesh": [
        "I love backend development and API design",
        "I'm learning about cloud computing and AWS",
        "I enjoy reading tech blogs and staying updated with trends",
        "My hobby is photography and traveling"
    ],
    "satvik": [
        "I'm interested in AI ",
        "I enjoy playing video games in my free time",
        "I'm learning about blockchain technology",
        "My favorite sport is basketball"
    ]
}

with st.sidebar:
    st.header("🔑 Settings")
    
    # User selection with predefined names and custom option
    predefined_users = ["shubham", "aaryan", "prathmesh", "satvik"]
    user_options = predefined_users + ["➕ Create New User"]
    
    selected_option = st.selectbox("Select User", user_options, index=0)
    
    if selected_option == "➕ Create New User":
        user_id = st.text_input("Enter new user name:", placeholder="e.g., john, sarah, alex...")
        if not user_id:
            st.warning("⚠️ Please enter a user name to continue")
            user_id = "temp_user"  # Fallback to prevent errors
    else:
        user_id = selected_option
    
    agent_id = st.text_input("Agent ID (optional)")
    run_id = st.text_input("Run ID (optional)")
    default_category = st.text_input("Default Metadata Category (optional)")

    # Check for API keys in environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY")
    mem0_api_key = os.getenv("MEM0_API_KEY")
    
    # Display API key status
    if openai_api_key:
        st.success("✅ OpenAI API Key found")
    else:
        st.error("❌ OpenAI API Key not found in environment")
    
    if mem0_api_key:
        st.success("✅ Mem0 API Key found")
    else:
        st.error("❌ Mem0 API Key not found in environment")


# ------------------ Initialize Components ------------------
@st.cache_resource
def initialize_mem0():
    """Initialize and return the Mem0 client."""
    mem0_key = os.getenv("MEM0_API_KEY")
    if not mem0_key:
        return None

    try:
        mem0_client = MemoryClient()
        return mem0_client
    except Exception as e:
        st.error(f"⚠️ Mem0 initialization failed: {str(e)}")
        return None

@st.cache_resource
def initialize_openai():
    """Initialize and return the OpenAI client."""
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        return None
    try:
        client = OpenAI()
        return client
    except Exception as e:
        st.error(f"⚠️ Failed to initialize OpenAI: {str(e)}")
        return None

# ------------------ Load Components ------------------
mem0_client = initialize_mem0()
openai_client = initialize_openai()

if mem0_client is not None:

    # ------------------ Memory Management ------------------
    st.sidebar.divider()
    st.sidebar.header("🧠 Memory Management")

    if mem0_client is None:
        st.sidebar.error("⚠️ Memory client not initialized. Check your Mem0 API Key.")
    else:
        memory_action = st.sidebar.selectbox("Action", ["View Memories", "Clear Memories"])  # Add handled in main area

        # View Memories
        if memory_action == "View Memories":
            try:
                filters = {"AND": [{"user_id": user_id}]}
                memories = mem0_client.get_all(version="v2", filters=filters, page=1, page_size=50)
                if memories and memories.get("count", 0) > 0:
                    st.sidebar.markdown("### Stored Memories:")
                    for memory in memories["results"]:
                        st.sidebar.markdown(f"- {memory['memory']}")
                else:
                    st.sidebar.info("ℹ️ No memories found.")
            except Exception as e:
                st.sidebar.error(f"❌ Failed to fetch memories: {str(e)}")

        # Clear Memories
        elif memory_action == "Clear Memories":
            try:
                mem0_client.delete_all(user_id=user_id)
                st.sidebar.success("🗑️ All memories cleared!")
            except Exception as e:
                st.sidebar.error(f"❌ Failed to clear memories: {str(e)}")

    # ------------------ User Info Section ------------------
    st.subheader(f"👤 Current User: {user_id.title()}")
    
    # Show current memory count
    try:
        filters = {"AND": [{"user_id": user_id}]}
        memories = mem0_client.get_all(version="v2", filters=filters, page=1, page_size=50)
        current_count = memories.get("count", 0) if memories else 0
        st.metric("Stored Memories", current_count)
    except:
        st.metric("Stored Memories", "Error")

    st.divider()

    # ------------------ Chatbot (Main Area) ------------------
    st.subheader("💬 Chatbot")
    st.markdown("Chat with an AI that uses your stored memories for context. Responses and new insights will be saved back to memory.")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []  # list of {role, content}

    # Display existing chat
    for m in st.session_state.chat_messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    chat_input = st.chat_input("Message the assistant...")
    if chat_input and mem0_client is not None and openai_client is not None:
        # Show user message
        st.session_state.chat_messages.append({"role": "user", "content": chat_input})
        with st.chat_message("user"):
            st.markdown(chat_input)

        # Retrieve relevant memories
        # Retrieve relevant memories (Mem0 v2)
        try:
            filters = {"AND": [{"user_id": user_id}]}
            search_res = mem0_client.search(
                query=chat_input,
                version="v2",
                filters=filters,
                top_k=3,          # v2 uses top_k (not limit)
                rerank=False,     # optional
                threshold=0.3     # optional default
            )
            results = search_res.get("results", []) if isinstance(search_res, dict) else search_res
            memories_str = "\n".join(f"- {entry['memory']}" for entry in results)
        except Exception as e:
            st.warning(f"Mem0 search failed: {e}")
            memories_str = ""


        # Build messages and call OpenAI
        system_prompt = (
            "You are a helpful AI. Answer the user based on their query and the provided memories.\n"
            f"User Memories:\n{memories_str}"
        )
        messages_for_llm = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": chat_input},
        ]

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    completion = openai_client.chat.completions.create(
                        model="gpt-4o",  
                        messages=messages_for_llm,
                    )
                    assistant_response = completion.choices[0].message.content
                    st.markdown(assistant_response)
                except Exception as e:
                    assistant_response = f"⚠️ Failed to generate response: {str(e)}"
                    st.error(assistant_response)

        # Append assistant message and store conversation to memory
        st.session_state.chat_messages.append({"role": "assistant", "content": assistant_response})
        try:
            convo_messages = [
                {"role": "user", "content": chat_input},
                {"role": "assistant", "content": assistant_response},
            ]
            add_kwargs = {"user_id": user_id}
            if agent_id:
                add_kwargs["agent_id"] = agent_id
            if run_id:
                add_kwargs["run_id"] = run_id
            mem0_client.add(convo_messages, **add_kwargs)
        except Exception:
            pass

    # ------------------ Add Memory (Main Area) ------------------
    st.subheader(f"📝 Add Memory for {user_id.title()}")
    st.markdown(f"Enter text below to store it as a memory for **{user_id}** using Mem0. Optionally provide metadata.")

    with st.form("add_memory_form", clear_on_submit=True):
        user_text = st.text_area("Your text", height=120, placeholder="e.g., I'm planning to watch a movie tonight. Any recommendations?")
        category = st.text_input("Metadata Category (optional)", value=default_category)
        col1, col2 = st.columns(2)
        with col1:
            include_agent = st.checkbox("Include Agent/Run IDs if provided", value=True)
        with col2:
            submit_add = st.form_submit_button("Add to Memory")

    if submit_add and user_text and mem0_client is not None:
        try:
            messages = [
                {"role": "user", "content": user_text}
            ]

            add_kwargs = {"user_id": user_id}
            if include_agent and agent_id:
                add_kwargs["agent_id"] = agent_id
            if include_agent and run_id:
                add_kwargs["run_id"] = run_id
            metadata = {"category": category} if category else None

            if metadata:
                add_kwargs["metadata"] = metadata

            result = mem0_client.add(messages, **add_kwargs)
            st.success("✅ Memory added successfully!")
            with st.expander("Show API payload"):
                st.write({"messages": messages, **add_kwargs})
            with st.expander("Show result"):
                st.write(result)
        except Exception as e:
            st.error(f"❌ Failed to add memory: {str(e)}")
else:
    st.info("ℹ️ Please set your OPENAI_API_KEY and MEM0_API_KEY environment variables to get started.")
  

