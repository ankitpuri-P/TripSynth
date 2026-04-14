import streamlit as st
import re
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun 
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# --- 1. UI STYLING & BRANDING ---
st.markdown("""
<style>
/* TRON Glow Animation */
@keyframes tronGlow {
    0%   { color: #00ffff; text-shadow: 0 0 10px #00ffff; }
    33%  { color: #00ff99; text-shadow: 0 0 15px #00ff99; }
    66%  { color: #ffcc00; text-shadow: 0 0 20px #ffcc00; }
    100% { color: #ff0033; text-shadow: 0 0 25px #ff0033; }
}

/* Main heading */
.glow-text {
    font-size: 3.5rem;
    font-weight: 700;
    animation: tronGlow 6s infinite alternate;
}

/* Sub heading */
.glow-sub {
    font-size: 3.5rem;
    animation: tronGlow 8s infinite alternate;
}

html, body, [class*="css"]  {
    background-color: #000000 ;
}

/* Main app */
.stApp {
    background: radial-gradient(circle at top, #0a0f2c, #000000 70%);
}

/* Fix top header strip */
header {
    background: transparent !important;
}

/* Fix bottom input area */
footer {
    background: transparent !important;
}

/* Fix main container */
.block-container {
    background: transparent !important;
    padding-top: 2rem;
    max-width: 1200px !important; 
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #000000, #0a0f2c);
}

/* Chat bubbles */
.stChatMessage {
    background: rgba(17,17,17,0.8);
    border: 1px solid #00ffff33;
    box-shadow: 0 0 10px #00ffff22;
    border-radius: 12px;
    width: 100% !important;
}
            
/* Remove hidden Streamlit bars */
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stBottom"] {
    background: transparent !important;
}
            
/* 🛠️ ALIGNMENT FIXES */
/* Remove Streamlit's hidden width restriction on the text inside the chat */
[data-testid="stChatMessageContent"] {
    width: 100% !important;
    max-width: 100% !important; 
}

/* 📦 Grid container */
.itinerary-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    margin: 10px auto; 
    width: 96%; 
}

/* 🔥 Card Styling */
.itinerary-card {
    background: rgba(0, 255, 255, 0.05);
    border: 1px solid rgba(0, 255, 255, 0.3);
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 0 10px rgba(0, 255, 255, 0.1);
    line-height: 1.6;
}

/* 🔥 Title Styling */
.itinerary-title {
    color: #00ffff;
    font-size: 1.2rem;
    font-weight: bold;
    margin-bottom: 10px;
    border-bottom: 1px solid rgba(0, 255, 255, 0.3);
    padding-bottom: 5px;
}

/* Make it responsive (mobile) */
@media (max-width: 768px) {
    .itinerary-grid {
        grid-template-columns: 1fr;
        width: 100%;
    }
}
</style>
""", unsafe_allow_html=True)

# --- 2. THE WELCOME SCREEN (NAME GATEKEEPER) ---
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# If the user hasn't entered their name yet, show the login/welcome screen
if st.session_state.user_name == "":
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 4rem; color:#00ffff; text-shadow: 0 0 15px #00ffff;'>TripSynth ⚡</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray; font-size: 1.2rem;'>Synthesize your perfect journey.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name_input = st.text_input("What should I call you?", placeholder="Enter your first name...")
        if st.button("Start Exploring", use_container_width=True) and name_input:
            st.session_state.user_name = name_input
            st.rerun()
    st.stop() 

# --- 3. MULTI-CHAT MEMORY SETUP ---
if "chats" not in st.session_state:
    st.session_state.chats = {"New Expedition": []}
if "active_chat" not in st.session_state:
    st.session_state.active_chat = "New Expedition"

# --- 4. THE SIDEBAR ---
with st.sidebar:
    st.title("⚡ TripSynth")
    st.caption("Your AI Travel Engine")
    
    if st.button("➕ New Expedition", use_container_width=True):
        new_chat_name = f"New Expedition {len(st.session_state.chats) + 1}"
        st.session_state.chats[new_chat_name] = []
        st.session_state.active_chat = new_chat_name
        st.rerun() 

    st.divider()
    st.write("### History")
    
    for chat_name in st.session_state.chats.keys():
        if st.button(chat_name, use_container_width=True):
            st.session_state.active_chat = chat_name
            st.rerun()

# --- 5. MAIN CHAT UI ---
is_empty_chat = len(st.session_state.chats[st.session_state.active_chat]) == 0

if is_empty_chat:
    st.markdown(f"""
        <h1 class="glow-text">Hi {st.session_state.user_name}</h1>
        <h1 class="glow-sub">Where should we start?</h1>
        <br><br>
    """, unsafe_allow_html=True)
else:
    st.title(f"🧭 {st.session_state.active_chat}")

# Render messages
for msg in st.session_state.chats[st.session_state.active_chat]:
    with st.chat_message(msg["role"]):

        # 👤 USER MESSAGE
        if msg["role"] == "user":
            st.write(msg["content"])

        # 🤖 ASSISTANT MESSAGE (card layout)
        else:
            content = msg["content"]
            content = re.sub(r'<.*?>', '', content)
            content = re.sub(r'\n+', '\n', content).strip()
            
            # Split by Day
            if not re.search(r'Day\s*\d+', content):
                # Normal response (no itinerary)
                st.write(content)
            else:
                days = re.split(r'Day\s*\d+:', content)
                
                # Intro text
                intro_text = days[0].strip()
                if intro_text:
                    st.write(intro_text)
                
                cards_html = ""
                
                for i in range(1, len(days)):
                    day_content = days[i].strip()
                    
                    if day_content == "":
                        continue
                    
                    # Split the day's content into separate lines
                    day_lines = day_content.split('\n')
                    formatted_lines = []
                    
                    for line in day_lines:
                        line = line.strip()
                        if not line:
                            continue
                            
                        if ":" in line and "|" in line:
                            try:
                                time_part, rest = line.split(":", 1)
                                loc_part, desc_part = rest.split("|", 1)
                                
                                loc_clean = loc_part.strip()
                                desc_clean = desc_part.strip()
                                
                                # Generate the Universal Google Maps Link 
                                map_query = loc_clean.replace(' ', '+')
                                map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"
                                
                                # glowing green button CSS
                                map_link = f"<a href='{map_url}' target='_blank' style='color:#00ff99; text-decoration:none; font-size:0.85em; border: 1px solid #00ff99; padding: 2px 8px; border-radius: 4px; margin-left: 10px; transition: 0.3s;'>📍 Map</a>"
                                
                                # Assign the right icon
                                if "Morning" in time_part: icon = "🌅"
                                elif "Afternoon" in time_part: icon = "🌇"
                                elif "Evening" in time_part: icon = "🌙"
                                else: icon = "📌"
                                
                                formatted_lines.append(f"<b>{icon} {time_part.strip()}:</b> <span style='color:#ffcc00; font-weight:bold;'>{loc_clean}</span> {map_link}<br>{desc_clean}")
                            except Exception:
                                formatted_lines.append(line)
                        else:
                            formatted_lines.append(line)

                    day_html = "<br><br>".join(formatted_lines)

                    cards_html += f"""
<div class="itinerary-card">
    <div class="itinerary-title">Day {i}</div>
    <div>{day_html}</div>
</div>
"""

                st.markdown(f"""
<div class="itinerary-grid">
{cards_html}
</div>
""", unsafe_allow_html=True)


# --- 6. THE CHATBOT LOGIC ---
user_query = st.chat_input("Where do you want to go next? ✈️")

if user_query:
    st.session_state.chats[st.session_state.active_chat].append({"role": "user", "content": user_query})
    
    with st.chat_message("user"):
        st.write(user_query)

    with st.spinner("Synthesizing your itinerary..."):
        
        llm = ChatGroq(
            api_key=st.secrets["GROQ_API_KEY"],
            model="llama-3.3-70b-versatile",
            temperature=0
        )

        # --- AUTO-NAMING ---
        if len(st.session_state.chats[st.session_state.active_chat]) == 1 and st.session_state.active_chat.startswith("New Expedition"):
            try:
                title_prompt = f"Generate a short 2 to 4 word title for a travel plan based on this request: '{user_query}'. Return ONLY the title, no quotes, no extra text."
                new_title = llm.invoke(title_prompt).content.strip(' "')
                
                if new_title in st.session_state.chats:
                    new_title = f"{new_title} ({len(st.session_state.chats) + 1})"
                
                old_name = st.session_state.active_chat
                st.session_state.chats[new_title] = st.session_state.chats.pop(old_name)
                st.session_state.active_chat = new_title
            except Exception as e:
                pass 

        search_tool = DuckDuckGoSearchRun()
        tools = [search_tool]

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are TripSynth, a smart, modern AI travel concierge.

            Your ONLY job is to give HIGH-QUALITY, PRACTICAL, and NON-REPETITIVE travel advice.

            🚨 CRITICAL GUARDRAIL (STAY ON TOPIC):
            If the user asks about ANYTHING completely unrelated to travel, geography, or culture (e.g., coding, math, physics, general trivia like "what is merge sort"):
            - Politely decline to answer.
            - Remind them you are a specialized travel assistant.
            - Ask where they want to travel next.

            📝 CRITICAL FORMATTING RULE FOR ITINERARIES:
            To ensure the UI renders correctly, you MUST format itineraries exactly like this. 
            Do NOT put extra words next to the Day number.
            For the activities, you MUST provide the Exact Location Name, followed by the "|" symbol, followed by the description.

            Example Format:
            Day 1:
            Morning: Shaniwar Wada | Start your day exploring this historic fort...
            Afternoon: Raja Kelkar Museum | Discover amazing artifacts...
            Evening: Koregaon Park | Enjoy dinner and drinks in this lively area...

            Day 2:
            Morning: [Location Name] | [Activity Description]
            ...

            STEP 1: SEARCHING (If needed)
            If you need to look up live information, use your search tool. Stay completely silent while searching. Only output the tool command.

            STEP 2: FINAL ANSWER
            Write your natural, conversational response based on the guidelines above. Do NOT include any image tags or search commands in your final output."""),
            
            MessagesPlaceholder(variable_name="chat_history"), 
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"), 
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        langchain_history = []
        for msg in st.session_state.chats[st.session_state.active_chat][:-1]: 
            if msg["role"] == "user":
                langchain_history.append(HumanMessage(content=msg["content"]))
            else:
                langchain_history.append(AIMessage(content=msg["content"]))

        response = agent_executor.invoke({
            "input": user_query,
            "chat_history": langchain_history
        })

        # Simplified Parser 
        output_text = response["output"]

        st.session_state.chats[st.session_state.active_chat].append({
            "role": "assistant", 
            "content": output_text
        })
        
        st.rerun()