import streamlit as st
import re

from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# ============================================================
# 1. UI STYLING & BRANDING
# ============================================================

st.markdown("""
<style>
@keyframes tronGlow {
    0% { color: #00ffff; text-shadow: 0 0 10px #00ffff; }
    33% { color: #00ff99; text-shadow: 0 0 15px #00ff99; }
    66% { color: #ffcc00; text-shadow: 0 0 20px #ffcc00; }
    100% { color: #ff0033; text-shadow: 0 0 25px #ff0033; }
}

.glow-text {
    font-size: 3.5rem;
    font-weight: 700;
    animation: tronGlow 6s infinite alternate;
}

.glow-sub {
    font-size: 3.5rem;
    animation: tronGlow 8s infinite alternate;
}

html, body, [class*="css"] {
    background-color: #000000;
}

.stApp {
    background: radial-gradient(circle at top, #0a0f2c, #000000 70%);
}

header { background: transparent !important; }
footer { background: transparent !important; }

.block-container {
    background: transparent !important;
    padding-top: 2rem;
    max-width: 1200px !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #000000, #0a0f2c);
}

.stChatMessage {
    background: rgba(17, 17, 17, 0.8);
    border: 1px solid #00ffff33;
    box-shadow: 0 0 10px #00ffff22;
    border-radius: 12px;
    width: 100% !important;
}

[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stBottom"] {
    background: transparent !important;
}

[data-testid="stChatMessageContent"] {
    width: 100% !important;
    max-width: 100% !important;
}

.itinerary-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    margin: 10px auto;
    width: 96%;
}

.itinerary-card {
    background: rgba(0, 255, 255, 0.05);
    border: 1px solid rgba(0, 255, 255, 0.3);
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 0 10px rgba(0, 255, 255, 0.1);
    line-height: 1.6;
}

.itinerary-title {
    color: #00ffff;
    font-size: 1.2rem;
    font-weight: bold;
    margin-bottom: 10px;
    border-bottom: 1px solid rgba(0, 255, 255, 0.3);
    padding-bottom: 5px;
}

@media (max-width: 768px) {
    .itinerary-grid {
        grid-template-columns: 1fr;
        width: 100%;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 2. WELCOME SCREEN
# ============================================================

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if st.session_state.user_name == "":
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 4rem; color:#00ffff; text-shadow: 0 0 15px #00ffff;'>TripSynth ⚡</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray; font-size: 1.2rem;'>Synthesize your perfect journey.</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name_input = st.text_input("What should I call you?", placeholder="Enter your first name...")
        if st.button("Start Exploring", use_container_width=True) and name_input:
            st.session_state.user_name = name_input.strip()
            st.rerun()
    st.stop()

# ============================================================
# 3. CHAT MEMORY
# ============================================================

if "chats" not in st.session_state:
    st.session_state.chats = {"New Expedition": []}

if "active_chat" not in st.session_state:
    st.session_state.active_chat = "New Expedition"

# ============================================================
# 4. SIDEBAR
# ============================================================

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

# ============================================================
# 5. MAIN CHAT UI
# ============================================================

current_chat = st.session_state.chats[st.session_state.active_chat]
is_empty_chat = len(current_chat) == 0

if is_empty_chat:
    st.markdown(f"""
        <h1 class="glow-text">Hi {st.session_state.user_name}</h1>
        <h1 class="glow-sub">Where should we start?</h1>
        <br><br>
    """, unsafe_allow_html=True)
else:
    st.title(f"🧭 {st.session_state.active_chat}")

# ============================================================
# 6. RENDER CHAT HISTORY
# ============================================================

for msg in current_chat:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.write(msg["content"])
        else:
            content = msg["content"]
            content = re.sub(r"<.*?>", "", content)
            content = re.sub(r"\n+", "\n", content).strip()

            # Normal Response
            if not re.search(r"Day\s*\d+", content):
                st.write(content)
            # Itinerary Response
            else:
                days = re.split(r"Day\s*\d+:", content)
                intro_text = days[0].strip()

                if intro_text:
                    st.write(intro_text)

                cards_html = ""

                for i in range(1, len(days)):
                    day_content = days[i].strip()
                    if not day_content:
                        continue

                    day_lines = day_content.split("\n")
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
                                map_query = loc_clean.replace(" ", "+")
                                map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"

                                # Single line to prevent markdown code block formatting
                                map_link = f"<a href='{map_url}' target='_blank' style='color:#00ff99; text-decoration:none; font-size:0.85em; border:1px solid #00ff99; padding:2px 8px; border-radius:4px; margin-left:10px;'>📍 Map</a>"

                                if "Morning" in time_part: icon = "🌅"
                                elif "Afternoon" in time_part: icon = "🌇"
                                elif "Evening" in time_part: icon = "🌙"
                                else: icon = "📌"

                                # Single line to prevent markdown code block formatting
                                formatted_lines.append(f"<b>{icon} {time_part.strip()}:</b> <span style='color:#ffcc00; font-weight:bold;'>{loc_clean}</span> {map_link}<br>{desc_clean}")
                            except Exception:
                                formatted_lines.append(line)
                        else:
                            formatted_lines.append(line)

                    day_html = "<br><br>".join(formatted_lines)

                    # Flush left to prevent markdown code block formatting
                    cards_html += f"""
<div class="itinerary-card">
    <div class="itinerary-title">Day {i}</div>
    <div>{day_html}</div>
</div>
"""
                # Flush left to prevent markdown code block formatting
                st.markdown(f"""
<div class="itinerary-grid">
{cards_html}
</div>
""", unsafe_allow_html=True)

# ============================================================
# 7. WEB SEARCH TOOL
# ============================================================

@tool
def web_search(query: str) -> str:
    """
    Search the internet for up-to-date travel information,
    locations, attractions, restaurants, transportation,
    and weather.

    Args:
        query: The specific search query string to look up.
    """
    search = DuckDuckGoSearchRun()
    return search.run(query)

# ============================================================
# 8. CHAT INPUT
# ============================================================

user_query = st.chat_input("Where do you want to go next? ✈️")

if user_query:
    st.session_state.chats[st.session_state.active_chat].append({"role": "user", "content": user_query})

    with st.chat_message("user"):
        st.write(user_query)

    with st.spinner("Synthesizing your itinerary..."):
        try:
            # =================================================
            # GROQ MODEL
            # =================================================
            llm = ChatGroq(
                api_key=st.secrets["GROQ_API_KEY"],
                model="openai/gpt-oss-20b",
                temperature=0
            )

            # =================================================
            # AUTO-NAMING
            # =================================================
            if len(st.session_state.chats[st.session_state.active_chat]) == 1 and st.session_state.active_chat.startswith("New Expedition"):
                try:
                    title_prompt = f"Generate a short 2 to 4 word title for a travel plan based on this request: '{user_query}'. Return ONLY the title, no quotes, no extra text."
                    title_response = llm.invoke([HumanMessage(content=title_prompt)])
                    new_title = title_response.content.strip(' "')
                    
                    if not new_title:
                        new_title = "Travel Plan"
                    if new_title in st.session_state.chats:
                        new_title = f"{new_title} ({len(st.session_state.chats) + 1})"
                        
                    old_name = st.session_state.active_chat
                    st.session_state.chats[new_title] = st.session_state.chats.pop(old_name)
                    st.session_state.active_chat = new_title
                except Exception:
                    pass

            # =================================================
            # TOOLS & PROMPT
            # =================================================
            tools = [web_search]
            prompt = ChatPromptTemplate.from_messages([
                ("system", """
You are TripSynth, a smart, modern AI travel concierge.

Your ONLY job is to give HIGH-QUALITY, PRACTICAL, and NON-REPETITIVE travel advice.

==================================================
TRAVEL GUARDRAIL
==================================================
If the user asks about anything completely unrelated to travel, geography, or culture:
- Politely decline to answer.
- Remind them that you are a specialized travel assistant.
- Ask where they want to travel next.

==================================================
ITINERARY FORMATTING
==================================================
When creating an itinerary, use exactly this format:

Day 1:
Morning: Location Name | Activity Description
Afternoon: Location Name | Activity Description
Evening: Location Name | Activity Description

Day 2:
Morning: Location Name | Activity Description
...

IMPORTANT:
- Always write "Day 1:", "Day 2:", etc.
- Do not put extra text beside the Day number.
- Always provide the exact location name.
- Always put "|" between location and description.
- Keep descriptions practical and useful.

==================================================
WEB SEARCH
==================================================
Use the web search tool when current information is needed.
If web search is not necessary, answer directly.
Do NOT show search commands to the user.

==================================================
FINAL RESPONSE
==================================================
Your final answer should be natural, conversational, practical, and concise.
Do NOT include tool commands, image tags, internal reasoning, or search commands.
Focus entirely on helping the user plan their trip.
"""),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])

            # =================================================
            # CREATE AGENT
            # =================================================
            agent = create_tool_calling_agent(llm, tools, prompt)
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

            # =================================================
            # BUILD CHAT HISTORY
            # =================================================
            langchain_history = []
            previous_messages = st.session_state.chats[st.session_state.active_chat][:-1]

            for msg in previous_messages:
                if msg["role"] == "user":
                    langchain_history.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    langchain_history.append(AIMessage(content=msg["content"]))

            # =================================================
            # RUN AGENT
            # =================================================
            response = agent_executor.invoke({
                "input": user_query,
                "chat_history": langchain_history
            })
            
            output_text = response["output"]

            st.session_state.chats[st.session_state.active_chat].append({
                "role": "assistant",
                "content": output_text
            })
            
            st.rerun()

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
