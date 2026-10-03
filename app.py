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

/* TRON Glow Animation */
@keyframes tronGlow {
    0% {
        color: #00ffff;
        text-shadow: 0 0 10px #00ffff;
    }

    33% {
        color: #00ff99;
        text-shadow: 0 0 15px #00ff99;
    }

    66% {
        color: #ffcc00;
        text-shadow: 0 0 20px #ffcc00;
    }

    100% {
        color: #ff0033;
        text-shadow: 0 0 25px #ff0033;
    }
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


/* Global background */
html,
body,
[class*="css"] {
    background-color: #000000;
}


/* Main app */
.stApp {
    background: radial-gradient(
        circle at top,
        #0a0f2c,
        #000000 70%
    );
}


/* Header */
header {
    background: transparent !important;
}


/* Footer */
footer {
    background: transparent !important;
}


/* Main container */
.block-container {
    background: transparent !important;
    padding-top: 2rem;
    max-width: 1200px !important;
}


/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #000000,
        #0a0f2c
    );
}


/* Chat bubbles */
.stChatMessage {
    background: rgba(17, 17, 17, 0.8);
    border: 1px solid #00ffff33;
    box-shadow: 0 0 10px #00ffff22;
    border-radius: 12px;
    width: 100% !important;
}


/* Remove hidden Streamlit bars */
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stBottom"] {
    background: transparent !important;
}


/* Chat message content */
[data-testid="stChatMessageContent"] {
    width: 100% !important;
    max-width: 100% !important;
}


/* ============================================================
   ITINERARY GRID
   ============================================================ */

.itinerary-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    margin: 10px auto;
    width: 96%;
}


/* Itinerary card */
.itinerary-card {
    background: rgba(0, 255, 255, 0.05);
    border: 1px solid rgba(0, 255, 255, 0.3);
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 0 10px rgba(0, 255, 255, 0.1);
    line-height: 1.6;
}


/* Itinerary title */
.itinerary-title {
    color: #00ffff;
    font-size: 1.2rem;
    font-weight: bold;
    margin-bottom: 10px;
    border-bottom: 1px solid rgba(0, 255, 255, 0.3);
    padding-bottom: 5px;
}


/* Mobile */
@media (max-width: 768px) {

    .itinerary-grid {
        grid-template-columns: 1fr;
        width: 100%;
    }

}

</style>
""", unsafe_allow_html=True)


# ============================================================
# 2. WELCOME SCREEN / NAME GATEKEEPER
# ============================================================

if "user_name" not in st.session_state:
    st.session_state.user_name = ""


if st.session_state.user_name == "":

    st.markdown(
        "<br><br><br><br>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <h1 style="
            text-align: center;
            font-size: 4rem;
            color:#00ffff;
            text-shadow: 0 0 15px #00ffff;
        ">
            TripSynth ⚡
        </h1>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style="
            text-align: center;
            color: gray;
            font-size: 1.2rem;
        ">
            Synthesize your perfect journey.
        </p>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        name_input = st.text_input(
            "What should I call you?",
            placeholder="Enter your first name..."
        )

        if (
            st.button(
                "Start Exploring",
                use_container_width=True
            )
            and name_input
        ):

            st.session_state.user_name = name_input.strip()

            st.rerun()

    st.stop()


# ============================================================
# 3. MULTI-CHAT MEMORY SETUP
# ============================================================

if "chats" not in st.session_state:

    st.session_state.chats = {
        "New Expedition": []
    }


if "active_chat" not in st.session_state:

    st.session_state.active_chat = "New Expedition"


# ============================================================
# 4. SIDEBAR
# ============================================================

with st.sidebar:

    st.title("⚡ TripSynth")

    st.caption("Your AI Travel Engine")


    # New expedition button
    if st.button(
        "➕ New Expedition",
        use_container_width=True
    ):

        new_chat_name = (
            f"New Expedition "
            f"{len(st.session_state.chats) + 1}"
        )

        st.session_state.chats[new_chat_name] = []

        st.session_state.active_chat = new_chat_name

        st.rerun()


    st.divider()

    st.write("### History")


    # Existing conversations
    for chat_name in st.session_state.chats.keys():

        if st.button(
            chat_name,
            use_container_width=True
        ):

            st.session_state.active_chat = chat_name

            st.rerun()


# ============================================================
# 5. MAIN CHAT UI
# ============================================================

is_empty_chat = (
    len(
        st.session_state.chats[
            st.session_state.active_chat
        ]
    ) == 0
)


# Welcome message
if is_empty_chat:

    st.markdown(
        f"""
        <h1 class="glow-text">
            Hi {st.session_state.user_name}
        </h1>

        <h1 class="glow-sub">
            Where should we start?
        </h1>

        <br><br>
        """,
        unsafe_allow_html=True
    )

else:

    st.title(
        f"🧭 {st.session_state.active_chat}"
    )


# ============================================================
# 6. RENDER CHAT HISTORY
# ============================================================

for msg in st.session_state.chats[
    st.session_state.active_chat
]:

    with st.chat_message(msg["role"]):


        # ----------------------------------------------------
        # USER MESSAGE
        # ----------------------------------------------------

        if msg["role"] == "user":

            st.write(msg["content"])


        # ----------------------------------------------------
        # ASSISTANT MESSAGE
        # ----------------------------------------------------

        else:

            content = msg["content"]


            # Remove HTML
            content = re.sub(
                r"<.*?>",
                "",
                content
            )


            # Remove excessive newlines
            content = re.sub(
                r"\n+",
                "\n",
                content
            ).strip()


            # ------------------------------------------------
            # NORMAL RESPONSE
            # ------------------------------------------------

            if not re.search(
                r"Day\s*\d+",
                content
            ):

                st.write(content)


            # ------------------------------------------------
            # ITINERARY RESPONSE
            # ------------------------------------------------

            else:

                days = re.split(
                    r"Day\s*\d+:",
                    content
                )


                # Intro text
                intro_text = days[0].strip()

                if intro_text:

                    st.write(intro_text)


                cards_html = ""


                # Process every day
                for i in range(
                    1,
                    len(days)
                ):

                    day_content = days[i].strip()


                    if day_content == "":
                        continue


                    day_lines = day_content.split(
                        "\n"
                    )

                    formatted_lines = []


                    # Process every activity
                    for line in day_lines:

                        line = line.strip()


                        if not line:
                            continue


                        # Expected format:
                        #
                        # Morning: Location | Description
                        #

                        if ":" in line and "|" in line:

                            try:

                                time_part, rest = (
                                    line.split(
                                        ":",
                                        1
                                    )
                                )


                                loc_part, desc_part = (
                                    rest.split(
                                        "|",
                                        1
                                    )
                                )


                                loc_clean = (
                                    loc_part.strip()
                                )

                                desc_clean = (
                                    desc_part.strip()
                                )


                                # Google Maps query
                                map_query = (
                                    loc_clean.replace(
                                        " ",
                                        "+"
                                    )
                                )


                                map_url = (
                                    "https://www.google.com/"
                                    "maps/search/?api=1"
                                    f"&query={map_query}"
                                )


                                # Google Maps button
                                map_link = f"""
                                <a
                                    href="{map_url}"
                                    target="_blank"
                                    style="
                                        color:#00ff99;
                                        text-decoration:none;
                                        font-size:0.85em;
                                        border:1px solid #00ff99;
                                        padding:2px 8px;
                                        border-radius:4px;
                                        margin-left:10px;
                                    "
                                >
                                    📍 Map
                                </a>
                                """


                                # Icons
                                if "Morning" in time_part:

                                    icon = "🌅"

                                elif "Afternoon" in time_part:

                                    icon = "🌇"

                                elif "Evening" in time_part:

                                    icon = "🌙"

                                else:

                                    icon = "📌"


                                formatted_lines.append(
                                    f"""
                                    <b>
                                        {icon}
                                        {time_part.strip()}:
                                    </b>

                                    <span style="
                                        color:#ffcc00;
                                        font-weight:bold;
                                    ">
                                        {loc_clean}
                                    </span>

                                    {map_link}

                                    <br>

                                    {desc_clean}
                                    """
                                )


                            except Exception:

                                formatted_lines.append(
                                    line
                                )


                        else:

                            formatted_lines.append(
                                line
                            )


                    # Build day card
                    day_html = "<br><br>".join(
                        formatted_lines
                    )


                    cards_html += f"""
                    <div class="itinerary-card">

                        <div class="itinerary-title">
                            Day {i}
                        </div>

                        <div>
                            {day_html}
                        </div>

                    </div>
                    """


                # Render itinerary
                st.markdown(
                    f"""
                    <div class="itinerary-grid">
                        {cards_html}
                    </div>
                    """,
                    unsafe_allow_html=True
                )


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

user_query = st.chat_input(
    "Where do you want to go next? ✈️"
)


if user_query:

    # ========================================================
    # SAVE USER MESSAGE
    # ========================================================

    st.session_state.chats[
        st.session_state.active_chat
    ].append(
        {
            "role": "user",
            "content": user_query
        }
    )


    # Show user message
    with st.chat_message("user"):

        st.write(user_query)


    # ========================================================
    # AI PROCESSING
    # ========================================================

    with st.spinner(
        "Synthesizing your itinerary..."
    ):


        # ----------------------------------------------------
        # GROQ LLM
        # ----------------------------------------------------

        llm = ChatGroq(

            api_key=st.secrets[
                "GROQ_API_KEY"
            ],

            # IMPORTANT:
            # llama3-8b-8192 is retired.
            #
            # This model supports tool calling.
            model="openai/gpt-oss-20b",

            temperature=0
        )


        # ====================================================
        # AUTO-NAMING
        # ====================================================

        if (
            len(
                st.session_state.chats[
                    st.session_state.active_chat
                ]
            ) == 1

            and

            st.session_state.active_chat.startswith(
                "New Expedition"
            )
        ):

            try:

                title_prompt = (
                    "Generate a short 2 to 4 word "
                    "title for a travel plan based "
                    f"on this request: '{user_query}'. "
                    "Return ONLY the title, "
                    "no quotes, no extra text."
                )


                title_response = llm.invoke(
                    [
                        HumanMessage(
                            content=title_prompt
                        )
                    ]
                )


                new_title = (
                    title_response.content
                    .strip(' "')
                )


                # Fallback
                if not new_title:

                    new_title = "Travel Plan"


                # Avoid duplicate names
                if (
                    new_title
                    in st.session_state.chats
                ):

                    new_title = (
                        f"{new_title} "
                        f"({len(st.session_state.chats) + 1})"
                    )


                old_name = (
                    st.session_state.active_chat
                )


                st.session_state.chats[
                    new_title
                ] = st.session_state.chats.pop(
                    old_name
                )


                st.session_state.active_chat = (
                    new_title
                )


            except Exception:

                # If auto-naming fails,
                # keep the original chat name.
                pass


        # ====================================================
        # TOOLS
        # ====================================================

        tools = [
            web_search
        ]


        # ====================================================
        # SYSTEM PROMPT
        # ====================================================

        prompt = ChatPromptTemplate.from_messages([

            (
                "system",

                """
You are TripSynth, a smart, modern AI travel concierge.

Your ONLY job is to give HIGH-QUALITY, PRACTICAL,
and NON-REPETITIVE travel advice.

==================================================
TRAVEL GUARDRAIL
==================================================

If the user asks about anything completely unrelated
to travel, geography, or culture:

- Politely decline to answer.
- Remind them that you are a specialized travel assistant.
- Ask where they want to travel next.

==================================================
ITINERARY FORMATTING
==================================================

When creating an itinerary, you MUST use exactly
this format:

Day 1:
Morning: Location Name | Activity Description
Afternoon: Location Name | Activity Description
Evening: Location Name | Activity Description

Day 2:
Morning: Location Name | Activity Description
Afternoon: Location Name | Activity Description
Evening: Location Name | Activity Description

IMPORTANT:

- Always write "Day 1:", "Day 2:", etc.
- Do not put extra text beside the Day number.
- Always provide the exact location name.
- Always put "|" between location and description.
- Keep descriptions practical and useful.
- Avoid repeating the same attraction unnecessarily.

==================================================
WEB SEARCH
==================================================

Use the web search tool when current information is
needed, such as:

- Current weather
- Current opening hours
- Current attractions
- Current travel information
- Current events
- Restaurants
- Transportation information
- Current prices when available

If web search is not necessary, answer directly.

Do NOT show search commands to the user.

==================================================
FINAL RESPONSE
==================================================

Your final answer should be natural,
conversational, practical, and concise.

Do NOT include:

- Tool commands
- Image tags
- Internal reasoning
- Search commands
- Technical implementation details

Focus entirely on helping the user plan their trip.
"""
            ),

            MessagesPlaceholder(
                variable_name="chat_history"
            ),

            (
                "human",
                "{input}"
            ),

            MessagesPlaceholder(
                variable_name="agent_scratchpad"
            )
        ])


        # ====================================================
        # CREATE AGENT
        # ====================================================

        try:

            agent = create_tool_calling_agent(
                llm,
                tools,
                prompt
            )


            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True
            )


            # =================================================
            # BUILD CHAT HISTORY
            # =================================================

            langchain_history = []


            previous_messages = (
                st.session_state.chats[
                    st.session_state.active_chat
                ][:-1]
            )


            for msg in previous_messages:

                if msg["role"] == "user":

                    langchain_history.append(
                        HumanMessage(
                            content=msg["content"]
                        )
                    )

                elif msg["role"] == "assistant":

                    langchain_history.append(
                        AIMessage(
                            content=msg["content"]
                        )
                    )


            # =================================================
            # RUN AGENT
            # =================================================

            response = agent_executor.invoke(
                {
                    "input": user_query,
                    "chat_history": langchain_history
                }
            )


            # Extract final response
            output_text = response["output"]


            # =================================================
            # SAVE ASSISTANT RESPONSE
            # =================================================

            st.session_state.chats[
                st.session_state.active_chat
            ].append(
                {
                    "role": "assistant",
                    "content": output_text
                }
            )


        # ====================================================
        # ERROR HANDLING
        # ====================================================

        except Exception as e:

            st.error(
                "⚠️ TripSynth couldn't generate "
                "a response right now."
            )

            st.exception(e)

            st.stop()


    # ========================================================
    # REFRESH UI
    # ========================================================

    st.rerun()

Important change

The main fix is this:

model="openai/gpt-oss-20b"

instead of:

model="llama3-8b-8192"

Your old model is retired, which is why entering "Goa" was reaching the Groq API and then dying with "BadRequestError".

Also make sure your Streamlit secrets still contain:

GROQ_API_KEY = "your_groq_api_key"

Then commit/push this "app.py" and redeploy your Streamlit app.