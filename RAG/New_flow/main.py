import streamlit as st
import asyncio
import tempfile
import os
import logging
from pathlib import Path

from rag_engine.process_query import ChatBot
from data_ingestion.ingest_data import save_document_data
from utils.settings import settings

from utils.main_utils import (
    setup_logger,
    clean_markdown_to_html,
    get_available_templates,
    agentic_template_selector,
    append_template_context,
    insert_template,
    create_enhanced_pdf,
    create_basic_pdf
)

# ------------------------
# Setup loggers
# ------------------------
if 'logger_initialized' not in st.session_state:
    setup_logger()
    st.session_state.logger_initialized = True

ingestion_logger = logging.getLogger("ingestion")
generation_logger = logging.getLogger("generation")

# ------------------------
# Custom CSS for sidebar
# ------------------------
st.markdown("""
<style>
    /* Sidebar button styling */
    .stSidebar .element-container .stButton > button {
        width: 100% !important;
        border: none !important;
        outline: none !important;
        border-radius: 2px !important;
        box-shadow: none !important;
        background-color: rgba(0, 0, 0, 0.05) !important;
        margin-bottom: 5px !important;
    }
    .stSidebar .element-container .stButton > button:hover,
    .stSidebar .element-container .stButton > button:focus,
    .stSidebar .element-container .stButton > button:active {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        background-color: rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Template gallery styling */
    .template-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        margin: 5px;
        text-align: center;
        background-color: #f9f9f9;
    }
    
    .template-card:hover {
        background-color: #f0f0f0;
        border-color: #007bff;
    }
</style>
""", unsafe_allow_html=True)


# ------------------------
# Sidebar with navigation
# ------------------------
with st.sidebar:
    # logo if exists
    if Path("rm_logo.png").exists():
        st.image("rm_logo.png", width=200)
    else:
        st.markdown("**RUGGED MONITORING**")

    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Chat"

    if st.button("Upload", key="upload_btn", use_container_width=True):
        st.session_state.active_tab = "Upload"

    if st.button("Chat", key="chat_btn", use_container_width=True):
        st.session_state.active_tab = "Chat"
    
    if st.button("Templates", key="templates_btn", use_container_width=True):
        st.session_state.active_tab = "Templates"

    if st.button("Make a Proposal", key="proposal_btn", use_container_width=True):
        st.session_state.active_tab = "Proposal"

    # Chat-specific controls
    if st.session_state.active_tab == "Chat":
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "metadata_history" not in st.session_state:
            st.session_state.metadata_history = []

        st.header("Chat Controls")
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.session_state.metadata_history = []
            st.rerun()


# ------------------------
# Templates Tab
# ------------------------
if st.session_state.active_tab == "Templates":
    st.title("📋 Template Gallery")
    
    templates = get_available_templates()
    
    if not templates:
        st.info("No templates found. Please add .png template files to the 'templates' folder.")
        st.markdown("**Expected template files:**")
        st.markdown("- `transformer.png` - For transformer-related queries")
        st.markdown("- `cable.png` - For cable-related queries")
        st.markdown("- `switch.png` - For switch-related queries")
        st.markdown("- Add more templates as needed...")
    else:
        st.markdown(f"Found **{len(templates)}** templates:")
        
        # Display templates in a grid
        cols = st.columns(3)
        for idx, (template_name, template_path) in enumerate(templates.items()):
            col = cols[idx % 3]
            with col:
                st.markdown(f"### {template_name.title()}")
                try:
                    st.image(str(template_path), caption=f"{template_name} template", use_container_width=True)
                    if st.button(f"Use {template_name}", key=f"use_{template_name}"):
                        st.session_state.active_tab = "Chat"
                        st.session_state.template_to_add = template_name
                        st.rerun()
                except Exception as e:
                    st.error(f"Could not load {template_name}: {e}")


# ------------------------
# Chat Tab
# ------------------------
elif st.session_state.active_tab == "Chat":
    generation_logger.info("Selected Chat button")
    st.title("RAG ChatBot")

    @st.cache_resource
    def get_chatbot():
        return ChatBot()

    chatbot = get_chatbot()

    # Display chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            # Show content (some responses may contain HTML tags; show as markdown)
            st.markdown(message["content"], unsafe_allow_html=True)
            
            # Display template if it was automatically detected and used
            if message["role"] == "assistant" and "template_used" in message:
                template_name = message["template_used"]
                template_path = get_available_templates().get(template_name)
                if template_path and template_path.exists():
                    with st.container():
                        st.markdown(f"**📋 {template_name.title()} Template:**")
                        st.image(str(template_path), caption=f"{template_name.title()} Reference Template", width=500)
            
            # Display sources (metadata_history aligned to assistant messages)
            if message["role"] == "assistant" and i < len(st.session_state.metadata_history) * 2:
                # metadata list appended per assistant response; attempt to align
                try:
                    metadata_index = len([m for m in st.session_state.messages[:i+1] if m["role"]=="assistant"]) - 1
                    metadata = st.session_state.metadata_history[metadata_index] if metadata_index < len(st.session_state.metadata_history) else None
                except Exception:
                    metadata = None
                if metadata and metadata.get("sources"):
                    with st.expander("📚 Sources", expanded=False):
                        for j, source in enumerate(metadata["sources"], 1):
                            st.write(f"**Source {j}:** {source.get('source')} (Page: {source.get('page')})")

    # New user input with template detection
    prompt = st.chat_input("Ask me about transformers, cables, switches, or any technical questions...")
    
    if prompt:
        # Check for manual template set from Templates tab
        detected_template = None
        if hasattr(st.session_state, 'template_to_add'):
            detected_template = st.session_state.template_to_add
            # use once and remove
            try:
                delattr(st.session_state, 'template_to_add')
            except Exception:
                st.session_state.pop('template_to_add', None)

        # If no manual template, try auto-detect by text
        if not detected_template:
            detected_template = agentic_template_selector(prompt)
            if detected_template == "none":
             detected_template = None
        
        # Show template detection notification
        # if detected_template:
        #     st.info(f"🔍 Detected query about: **{detected_template.title()}** - Template will be included in response")
        
        # If template detected, append context for better RAG response
        enhanced_prompt = append_template_context(prompt, detected_template) if detected_template else prompt

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing your question and retrieving relevant information..."):
                try:
                    # Use enhanced prompt for RAG query
                    response, metadata = asyncio.run(chatbot.run(enhanced_prompt))
                    # If you want to include the template image inline in assistant response HTML, you could:
                    # response_html = insert_template(response, detected_template) if detected_template else response
                    response_html = response  # keep textual response; display template separately below
                    st.markdown(response_html, unsafe_allow_html=True)
                    
                    # Store template info in message if template was detected
                    assistant_message = {"role": "assistant", "content": response_html}
                    if detected_template:
                        assistant_message["template_used"] = detected_template
                        # Display template image immediately after response
                        template_path = get_available_templates().get(detected_template)
                        if template_path and template_path.exists():
                            with st.container():
                                st.markdown(f"**📋 {detected_template.title()} Template:**")
                                st.image(str(template_path), caption=f"{detected_template.title()} Reference Template", width=500)
                    
                    # Append metadata and assistant message
                    st.session_state.metadata_history.append(metadata)
                    st.session_state.messages.append(assistant_message)

                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    st.session_state.metadata_history.append(None)


# ------------------------
# Upload Tab
# ------------------------
elif st.session_state.active_tab == "Upload":
    ingestion_logger.info("user selected Upload button")
    st.title("Upload PDF's")
    supported_formats = ["pdf"]
    uploaded_files = st.file_uploader("Upload files", type=supported_formats, accept_multiple_files=True)

    if uploaded_files:
        total_files = len(uploaded_files)
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text(f"Processed 0 out of {total_files} files.")

        for index, uploaded_file in enumerate(uploaded_files, start=1):
            file_name = uploaded_file.name
            file_format = file_name.lower().split(".")[-1]
            if file_format not in supported_formats:
                st.warning(f"Invalid file: {file_name}")
                continue

            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = os.path.join(temp_dir, file_name)
                with open(file_path, "wb") as new_temp_file:
                    new_temp_file.write(uploaded_file.read())

                try:
                    asyncio.run(save_document_data(temp_dir, actual_source=file_name))
                except Exception as e:
                    st.error(f"Skipping file {file_name}: {e}")

            progress_bar.progress(index / total_files)
            status_text.text(f"Processed {index} out of {total_files} files.")

        st.success("Files uploaded!")


# ------------------------
#  Proposal Tab
# ------------------------
elif st.session_state.active_tab == "Proposal":
    generation_logger.info("Selected Proposal button")
    st.title("✍️ Make a Proposal")

    if "proposal_messages" not in st.session_state:
        st.session_state.proposal_messages = []

    if "proposal_metadata" not in st.session_state:
        st.session_state.proposal_metadata = []

    @st.cache_resource
    def get_proposal_bot():
        return ChatBot()

    proposal_bot = get_proposal_bot()

    # Template insertion section
    st.subheader("📋 Insert Templates")
    templates = get_available_templates()
    
    if templates:
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_template = st.selectbox(
                "Choose a template to insert:", 
                ["Select template..."] + list(templates.keys()),
                key="proposal_template_select"
            )
        with col2:
            if st.button("Insert Template", disabled=(selected_template == "Select template...")):
                if selected_template != "Select template...":
                    st.session_state.template_to_insert = selected_template
                    st.success(f"Template '{selected_template}' will be added to your next proposal input!")
    else:
        st.info("No templates found in 'templates/' folder")

    st.divider()

    # Display previous proposal chat with templates
    for i, message in enumerate(st.session_state.proposal_messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)
            
            # Display template if it was used in this proposal message
            if message["role"] == "assistant" and "template_used" in message:
                template_name = message["template_used"]
                template_path = get_available_templates().get(template_name)
                if template_path and template_path.exists():
                    with st.container():
                        st.markdown(f"**📋 {template_name.title()} Template Reference:**")
                        st.image(str(template_path), caption=f"{template_name.title()} Specification Template", width=500)

    # Template insertion notification
    if hasattr(st.session_state, 'template_to_insert'):
        st.info(f"💡 Template '{st.session_state.template_to_insert}' will be included in your next proposal section.")

    # New proposal input with template integration
    proposal_prompt = st.chat_input("Write your proposal details here... (mention transformers, cables, etc. for automatic templates)")
    
    if proposal_prompt:
            # <<< ADDED: Reset if user explicitly mentions a new template
        template_keywords = ["gis template", "switchgear template", "transformer template", "cable template"]
        if any(keyword in proposal_prompt.lower() for keyword in template_keywords):
            st.session_state.proposal_messages = []
            st.session_state.proposal_metadata = []

        # Handle manual template insertion
        if hasattr(st.session_state, 'template_to_insert'):
            enhanced_proposal_prompt = append_template_context(proposal_prompt, st.session_state.template_to_insert)
            inserted_template = st.session_state.template_to_insert
            try:
                delattr(st.session_state, 'template_to_insert')
            except Exception:
                st.session_state.pop('template_to_insert', None)
        else:
            # Auto-detect template from proposal content
            detected_template = agentic_template_selector(proposal_prompt)
            if detected_template and detected_template != "none":
                enhanced_proposal_prompt = append_template_context(proposal_prompt, detected_template)
                inserted_template = detected_template
            else:
                enhanced_proposal_prompt = proposal_prompt
                inserted_template = None

        # Show detection notification
        if inserted_template:
            st.info(f"🔍 Including {inserted_template.title()} template in proposal")

        st.session_state.proposal_messages.append({"role": "user", "content": proposal_prompt})
        with st.chat_message("user"):
            st.markdown(proposal_prompt)

        with st.chat_message("assistant"):
            with st.spinner("Drafting proposal with template specifications..."):
                try:
                    # Use enhanced prompt with template context
                    response, metadata = asyncio.run(proposal_bot.run(enhanced_proposal_prompt))
                    # Display response
                    st.markdown(response, unsafe_allow_html=True)
                    
                    # Store template info if used
                    assistant_message = {"role": "assistant", "content": response}
                    if inserted_template:
                        assistant_message["template_used"] = inserted_template
                        # Display template image
                        template_path = get_available_templates().get(inserted_template)
                        if template_path and template_path.exists():
                            with st.container():
                                st.markdown(f"**📋 {inserted_template.title()} Template Reference:**")
                                st.image(str(template_path), caption=f"{inserted_template.title()} Specification Template", width=500)
                    
                    st.session_state.proposal_metadata.append(metadata)
                    st.session_state.proposal_messages.append(assistant_message)
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error while drafting proposal: {str(e)}"
                    st.error(error_msg)
                    st.session_state.proposal_messages.append({"role": "assistant", "content": error_msg})
                    st.session_state.proposal_metadata.append(None)

    # ------------------------------
    # Save Proposal Section
    # ------------------------------
    if st.session_state.proposal_messages:
        st.divider()
        st.subheader("💾 Save Your Proposal")

        # Combine assistant messages as draft
        draft_text = "\n\n".join(
            msg["content"] for msg in st.session_state.proposal_messages if msg["role"] == "assistant"
        )

        # Get all templates used in the proposal
        used_templates = []
        for msg in st.session_state.proposal_messages:
            if msg["role"] == "assistant" and "template_used" in msg:
                template_name = msg["template_used"]
                if template_name not in used_templates:
                    used_templates.append(template_name)

        if st.download_button("⬇️ Download Proposal as TXT", draft_text, file_name="proposal.txt"):
            st.success("Proposal downloaded as TXT!")

        # Enhanced PDF generation with templates and multi-page support via utils
        try:
            pdf_buffer = create_enhanced_pdf(draft_text, used_templates)
            if st.download_button("⬇️ Download Enhanced Proposal as PDF", 
                                pdf_buffer.getvalue(), 
                                file_name="proposal_with_templates.pdf", 
                                mime="application/pdf"):
                st.success("Enhanced PDF with templates downloaded!")
        except ImportError:
            st.info("Install required packages for enhanced PDF: pip install reportlab pillow")
            try:
                pdf_buffer = create_basic_pdf(draft_text)
                if st.download_button("⬇️ Download Basic Proposal as PDF", 
                                    pdf_buffer.getvalue(), 
                                    file_name="proposal_basic.pdf", 
                                    mime="application/pdf"):
                    st.success("Basic PDF downloaded!")
            except Exception as e:
                st.error(f"PDF generation failed: {e}")
        except Exception as e:
            st.error(f"Enhanced PDF generation failed: {e}")

