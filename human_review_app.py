#!/usr/bin/env python3
"""
Human Review Interface for LLM Responses

Run with: streamlit run human_review_app.py
"""

import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import csv
import re

# Import smart storage (auto-detects environment)
from smart_storage import SmartStorage

# Initialize storage
# - Local dev: Uses JSON file (fast, no setup)
# - Production: Uses MongoDB (persistent, set MONGODB_URI env var)
storage = SmartStorage()


def remove_highlighting(html_text: str) -> str:
    """Remove yellow/background-color highlighting from HTML text"""
    if not html_text:
        return html_text
    
    # Remove inline background-color styles from span tags
    # This pattern matches style attributes that contain background-color
    html_text = re.sub(
        r'<span\s+style="[^"]*background-color:\s*rgb\([^)]+\);[^"]*">(.*?)</span>',
        r'\1',
        html_text,
        flags=re.IGNORECASE
    )
    
    # Also handle cases where background-color is the only style
    html_text = re.sub(
        r'<span\s+style="background-color:\s*rgb\([^)]+\);">(.*?)</span>',
        r'\1',
        html_text,
        flags=re.IGNORECASE
    )
    
    return html_text


def load_pending_reviews() -> List[Dict]:
    """Load responses that need review"""
    pending_file = Path("review_data/pending_reviews.json")
    
    if not pending_file.exists():
        return []
    
    with open(pending_file) as f:
        return json.load(f)


def mark_as_reviewed(review_id: str):
    """Remove from pending after review"""
    pending_file = Path("review_data/pending_reviews.json")
    
    if not pending_file.exists():
        return
    
    with open(pending_file) as f:
        pending = json.load(f)
    
    # Remove the reviewed item
    pending = [r for r in pending if r.get('id') != review_id]
    
    with open(pending_file, 'w') as f:
        json.dump(pending, f, indent=2)


def main():
    st.set_page_config(
        page_title="Human Review",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for dark theme
    st.markdown("""
        <style>
        /* Dark theme */
        .stApp {
            background-color: #0e1117;
        }
        
        /* Hide default Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Custom styling */
        .main-title {
            font-size: 18px;
            color: #cccccc;
            margin-bottom: 20px;
        }
        
        .conversation-box {
            background-color: #1a1d24;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 3px solid #333;
        }
        
        .user-msg {
            color: #e0e0e0;
            font-size: 14px;
            margin-bottom: 10px;
        }
        
        .assistant-msg {
            color: #b0b0b0;
            font-size: 14px;
            background-color: #0e1117;
            padding: 12px;
            border-radius: 6px;
            margin-top: 8px;
        }
        
        .label-text {
            color: #888;
            font-size: 12px;
            margin-bottom: 8px;
            margin-top: 15px;
            font-weight: 500;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #1a1d24;
        }
        
        div[data-testid="stSidebar"] {
            background-color: #1a1d24;
        }
        
        /* Button styling */
        .stButton>button {
            background-color: #2d3139;
            color: white;
            border: none;
            border-radius: 6px;
        }
        
        .stButton>button:hover {
            background-color: #3d4149;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Top navigation tabs
    tab1, tab2 = st.tabs(["📝 Review", "📊 Results & Analytics"])
    
    with tab1:
        show_review_page()
    
    with tab2:
        show_results_page()


def show_review_page():
    """Main review interface"""
    
    # Load pending reviews
    pending = load_pending_reviews()
    
    if not pending:
        st.markdown('<p class="main-title">No pending reviews</p>', unsafe_allow_html=True)
        return
    
    # Get current review
    current_review = pending[0]
    review_id = current_review.get('id', '')
    
    # Top bar
    col_title, col_nav = st.columns([3, 1])
    with col_title:
        st.markdown(f'<p class="main-title">Human review - {len(pending)} of {len(pending)} remaining</p>', unsafe_allow_html=True)
    with col_nav:
        st.markdown(f'<p style="text-align: right; color: #666; font-size: 12px;">Item {1} of {len(pending)}</p>', unsafe_allow_html=True)
    
    # Layout: Conversation on left, Review form on right
    col1, col2 = st.columns([2.5, 1])
    
    with col1:
        # Conversation display        
        # Display prompt/user message
        st.markdown(f'''
        <p class="label-text">Project Title</p>
        <div class="conversation-box">
            <p class="user-msg">{current_review.get("prompt", "")}</p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Display context if exists
        if current_review.get('context'):
            context_html = f'<p class="user-msg" style="font-size: 12px; color: #888;">{current_review.get("context", "")}</p>'
            
            # Add agency user and organization if available
            if current_review.get('agency_user'):
                context_html += f'<p class="user-msg" style="font-size: 12px; color: #888; margin-top: 5px;">Agency User: {current_review.get("agency_user")}</p>'
            if current_review.get('organization_name'):
                context_html += f'<p class="user-msg" style="font-size: 12px; color: #888; margin-top: 5px;">Organization: {current_review.get("organization_name")}</p>'
            
            st.markdown(f'''
            <p class="label-text">Context</p>
            <div class="conversation-box">
                {context_html}
            </div>
            ''', unsafe_allow_html=True)
        
        # Display assistant response (with highlighting removed)
        response_text = remove_highlighting(current_review.get("response", ""))
        st.markdown(f'''
        <p class="label-text">Assistant</p>
        <div class="conversation-box">
            <div class="assistant-msg">{response_text}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Expected output if available
        if current_review.get('expected_output'):
            st.markdown('<div class="conversation-box">', unsafe_allow_html=True)
            st.markdown('<p class="label-text">Expected</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="user-msg" style="color: #4CAF50;">{current_review.get("expected_output", "")}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Scores")
        
        # Simple acceptable/not acceptable buttons
        col_acc, col_not = st.columns(2)
        with col_acc:
            acceptable = st.button("✓ Acceptable", use_container_width=True, key="btn_acceptable")
        with col_not:
            not_acceptable = st.button("✗ Not Acceptable", use_container_width=True, key="btn_not_acceptable")
        
        # Store the choice
        if 'score_choice' not in st.session_state:
            st.session_state.score_choice = None
        
        if acceptable:
            st.session_state.score_choice = "acceptable"
        elif not_acceptable:
            st.session_state.score_choice = "not_acceptable"
        
        if st.session_state.score_choice:
            choice_display = "✓ Acceptable" if st.session_state.score_choice == "acceptable" else "✗ Not Acceptable"
            st.info(f"Selected: {choice_display}")
        
        st.markdown("---")
        st.markdown("### Notes")
        
        # Free-form notes
        notes = st.text_area(
            "Notes",
            placeholder="Add your feedback here...",
            height=200,
            label_visibility="collapsed"
        )
        
        # Tags
        tags = st.multiselect(
            "Tags",
            ["good", "error", "hallucination", "needs-fix", "training-data"],
            default=[],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Action buttons
        if st.button("Submit Review", type="primary", use_container_width=True):
            # Validate selection
            if not st.session_state.get('score_choice'):
                st.error("Please select Acceptable or Not Acceptable")
                st.stop()
            
            # Save review
            review_data = {
                "review_id": review_id,
                "timestamp": datetime.now().isoformat(),
                "reviewer": st.session_state.get('reviewer_name', 'anonymous'),
                
                # Original data
                "prompt": current_review.get('prompt'),
                "context": current_review.get('context'),
                "response": current_review.get('response'),
                "expected_output": current_review.get('expected_output'),
                "model": current_review.get('model'),
                "feature": current_review.get('feature'),
                
                # Review data
                "acceptable": st.session_state.score_choice == "acceptable",
                "score_choice": st.session_state.score_choice,
                "notes": notes,
                "tags": tags
            }
            
            # Save to storage
            storage.save_review(review_data)
            
            # Mark as reviewed
            mark_as_reviewed(review_id)
            
            # Reset score choice for next review
            st.session_state.score_choice = None
            
            st.success("✓ Saved")
            
            # Move to next
            st.rerun()
        
        if st.button("Skip", use_container_width=True):
            # Move to end of queue
            pending.append(pending.pop(0))
            pending_file = Path("review_data/pending_reviews.json")
            with open(pending_file, 'w') as f:
                json.dump(pending, f, indent=2)
            st.rerun()


def show_results_page():
    """Results and Analytics page"""
    
    reviews = storage.get_all_reviews()
    
    if not reviews:
        st.info("No reviews yet. Start reviewing to see results here.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(reviews)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Reviews", len(df))
    
    with col2:
        acceptable_count = df['acceptable'].sum() if 'acceptable' in df.columns else 0
        acceptable_pct = (acceptable_count / len(df) * 100) if len(df) > 0 else 0
        st.metric("Acceptable", f"{acceptable_count}")
        st.caption(f"↑ {acceptable_pct:.0f}%")
    
    with col3:
        not_acceptable_count = len(df) - acceptable_count if 'acceptable' in df.columns else 0
        st.metric("Not Acceptable", f"{not_acceptable_count}")
    
    with col4:
        # Count unique organizations if available
        orgs_count = df['organization_name'].nunique() if 'organization_name' in df.columns else 0
        st.metric("Organizations", orgs_count)
    
    st.markdown("---")
    st.markdown("### Recent Reviews")
    
    # Prepare table data - show most important columns
    display_df = df.copy()
    
    # Sort by timestamp descending (newest first)
    if 'timestamp' in display_df.columns:
        display_df = display_df.sort_values('timestamp', ascending=False)
    
    # Create a clean table with key columns
    table_data = []
    for _, row in display_df.iterrows():
        # Truncate prompt for table display
        prompt = row.get('prompt', '')[:50] + '...' if len(str(row.get('prompt', ''))) > 50 else row.get('prompt', '')
        
        # Format timestamp to be more readable
        timestamp = row.get('timestamp', '')[:19] if row.get('timestamp') else ''
        
        # Format acceptable as checkmark
        acceptable = '✓' if row.get('acceptable', False) else '✗'
        
        # Get notes
        notes = row.get('notes', '')
        
        # Get tags as comma-separated string
        tags = ', '.join(row.get('tags', [])) if row.get('tags') else ''
        
        table_data.append({
            'project_title': prompt,
            'timestamp': timestamp,
            'acceptable': acceptable,
            'notes': notes,
            'tags': tags
        })
    
    # Display as dataframe with better column configuration
    table_df = pd.DataFrame(table_data)
    
    st.dataframe(
        table_df,
        column_config={
            "project_title": st.column_config.TextColumn(
                "Project Title",
                width="large",
            ),
            "timestamp": st.column_config.TextColumn(
                "Timestamp",
                width="medium",
            ),
            "acceptable": st.column_config.TextColumn(
                "Acceptable",
                width="small",
            ),
            "notes": st.column_config.TextColumn(
                "Notes",
                width="medium",
            ),
            "tags": st.column_config.TextColumn(
                "Tags",
                width="medium",
            ),
        },
        hide_index=True,
        use_container_width=True,
    )
    
    st.markdown("---")
    
    # Export buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Export for Fine-Tuning", use_container_width=True):
            # Format for fine-tuning
            finetuning_data = []
            for _, row in df.iterrows():
                finetuning_data.append({
                    "prompt": row.get('prompt', ''),
                    "completion": row.get('response', ''),
                    "metadata": {
                        "acceptable": row.get('acceptable', False),
                        "tags": row.get('tags', []),
                        "notes": row.get('notes', '')
                    }
                })
            
            json_data = json.dumps(finetuning_data, indent=2)
            st.download_button(
                label="Download Fine-Tuning Data",
                data=json_data,
                file_name=f"finetuning_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📥 Download All Reviews (JSON)", use_container_width=True):
            json_data = df.to_json(orient='records', indent=2)
            st.download_button(
                label="Download Reviews",
                data=json_data,
                file_name=f"reviews_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )


def show_history_page():
    """View review history"""
    st.header("📜 Review History")
    
    reviews = storage.get_all_reviews()
    
    if not reviews:
        st.info("No reviews yet. Start reviewing to see history here.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(reviews)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'rating' in df.columns:
            rating_filter = st.multiselect(
                "Filter by Rating",
                options=[1, 2, 3, 4, 5],
                default=[1, 2, 3, 4, 5]
            )
            df = df[df['rating'].isin(rating_filter)]
    
    with col2:
        if 'feature' in df.columns:
            features = df['feature'].unique()
            feature_filter = st.multiselect(
                "Filter by Feature",
                options=features,
                default=features
            )
            df = df[df['feature'].isin(feature_filter)]
    
    with col3:
        if 'tags' in df.columns:
            all_tags = set()
            for tags in df['tags']:
                if isinstance(tags, list):
                    all_tags.update(tags)
            
            tag_filter = st.multiselect(
                "Filter by Tags",
                options=list(all_tags)
            )
            
            if tag_filter:
                df = df[df['tags'].apply(lambda x: any(tag in x for tag in tag_filter) if isinstance(x, list) else False)]
    
    # Display table
    st.dataframe(
        df[['timestamp', 'rating', 'feature', 'model', 'notes', 'tags']],
        use_container_width=True,
        hide_index=True
    )
    
    # Download option
    st.markdown("---")
    
    # Export options
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export as CSV"):
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"reviews_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📥 Export as JSON"):
            json_data = df.to_json(orient='records', indent=2)
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name=f"reviews_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )


def show_analytics_page():
    """Analytics dashboard"""
    st.header("📊 Analytics")
    
    reviews = storage.get_all_reviews()
    
    if not reviews:
        st.info("No reviews yet. Analytics will appear here once you start reviewing.")
        return
    
    df = pd.DataFrame(reviews)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Reviews", len(df))
    
    with col2:
        if 'rating' in df.columns:
            avg_rating = df['rating'].mean()
            st.metric("Avg Rating", f"{avg_rating:.2f}")
    
    with col3:
        if 'criteria' in df.columns:
            accurate_pct = sum(r.get('criteria', {}).get('accurate', False) for r in reviews) / len(reviews) * 100
            st.metric("Accuracy Rate", f"{accurate_pct:.1f}%")
    
    with col4:
        if 'issues' in df.columns:
            issue_rate = sum(any(r.get('issues', {}).values()) for r in reviews) / len(reviews) * 100
            st.metric("Issue Rate", f"{issue_rate:.1f}%")
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Rating distribution
        if 'rating' in df.columns:
            st.subheader("Rating Distribution")
            rating_counts = df['rating'].value_counts().sort_index()
            st.bar_chart(rating_counts)
    
    with col2:
        # Issues breakdown
        st.subheader("Common Issues")
        issue_counts = {}
        for review in reviews:
            issues = review.get('issues', {})
            for issue_type, has_issue in issues.items():
                if has_issue:
                    issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        if issue_counts:
            issue_df = pd.DataFrame(list(issue_counts.items()), columns=['Issue', 'Count'])
            st.bar_chart(issue_df.set_index('Issue'))
    
    # Feature breakdown
    if 'feature' in df.columns and 'rating' in df.columns:
        st.markdown("---")
        st.subheader("Ratings by Feature")
        feature_ratings = df.groupby('feature')['rating'].agg(['mean', 'count'])
        st.dataframe(feature_ratings, use_container_width=True)
    
    # Timeline
    if 'timestamp' in df.columns:
        st.markdown("---")
        st.subheader("Reviews Over Time")
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_reviews = df.groupby('date').size()
        st.line_chart(daily_reviews)


# Reviewer identification
if 'reviewer_name' not in st.session_state:
    with st.sidebar:
        st.markdown("---")
        reviewer_name = st.text_input("Your Name (optional)", value="anonymous")
        st.session_state.reviewer_name = reviewer_name


if __name__ == '__main__':
    # Ensure directories exist
    Path("review_data").mkdir(exist_ok=True)
    
    main()

