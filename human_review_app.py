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


def reload_pending_reviews():
    """
    Reload pending reviews from the master backup file
    This allows multiple reviewers to review the same data
    
    Simple approach:
    1. Load from Postgres ONCE using load_from_postgres.py
    2. Keep a backup of those items
    3. Reload from backup when queue is empty
    """
    try:
        pending_file = Path("review_data/pending_reviews.json")
        backup_file = Path("review_data/master_reviews_backup.json")
        
        # If backup doesn't exist, create it from current pending
        if not backup_file.exists() and pending_file.exists():
            import shutil
            shutil.copy(pending_file, backup_file)
            return True, "✓ Created backup. Reload again to reset queue."
        
        # Reload from backup
        if backup_file.exists():
            import shutil
            shutil.copy(backup_file, pending_file)
            
            with open(backup_file) as f:
                items = json.load(f)
            
            return True, f"✓ Reloaded {len(items)} items from backup"
        else:
            return False, "No backup found. Please run load_from_postgres.py first."
            
    except Exception as e:
        return False, f"Error: {str(e)}"


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


def setup_controls_menu():
    """Setup controls menu in top right"""
    # Create columns to position the popover in top right
    col1, col2, col3 = st.columns([6, 1, 0.5])
    
    with col3:
        with st.popover("⚙️", use_container_width=True):
            st.markdown("### Settings")
            
            # Reviewer identification
            if 'reviewer_name' not in st.session_state:
                st.session_state.reviewer_name = 'anonymous'
            
            reviewer_name = st.text_input(
                "Your Name",
                value=st.session_state.reviewer_name,
                placeholder="Enter your name",
                key="reviewer_name_input"
            )
            st.session_state.reviewer_name = reviewer_name
            
            st.markdown("---")
            st.markdown("**🔄 Reset Queue**")
            st.caption("Reload items to allow multiple reviewers to review the same data")
            
            if st.button("🔄 Wipe & Reload Queue", use_container_width=True):
                with st.spinner("Reloading from database..."):
                    success, message = reload_pending_reviews()
                    if success:
                        st.success(message)
                        st.info("Queue reset! Multiple reviewers can now review the same items.")
                        st.rerun()
                    else:
                        st.error(message)
            
            st.markdown("---")
            
            # Show storage info
            storage_type = "MongoDB" if hasattr(storage.backend, 'db') else "JSON"
            st.caption(f"💾 Storage: {storage_type}")


def main():
    st.set_page_config(
        page_title="Human Review",
        page_icon="📝",
        layout="wide"
    )
    
    # Setup controls menu in top right
    setup_controls_menu()
    
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
        
        /* Reviewer input styling */
        .stTextInput input {
            background-color: #1a1d24 !important;
            border: 1px solid #333 !important;
            border-radius: 6px !important;
            color: #e0e0e0 !important;
            padding: 8px 12px !important;
            font-size: 13px !important;
        }
        
        .stTextInput input:focus {
            border-color: #555 !important;
            box-shadow: none !important;
        }
        
        /* Top bar spacing */
        .block-container {
            padding-top: 2rem !important;
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
        
        /* Fix barely visible metrics */
        [data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-size: 24px !important;
            font-weight: 600 !important;
        }
        
        [data-testid="stMetricLabel"] {
            color: #cccccc !important;
            font-size: 14px !important;
        }
        
        [data-testid="stMetricDelta"] {
            color: #aaaaaa !important;
        }
        
        /* Fix tab text visibility */
        .stTabs [data-baseweb="tab-list"] button {
            color: #cccccc !important;
        }
        
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            color: #ffffff !important;
        }
        
        /* Fix text input and text area */
        .stTextInput input, .stTextArea textarea {
            color: #ffffff !important;
            background-color: #1a1d24 !important;
        }
        
        /* Fix multiselect */
        .stMultiSelect [data-baseweb="select"] {
            color: #ffffff !important;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            color: #ffffff !important;
        }
        
        /* Popover styling for settings menu */
        [data-testid="stPopover"] {
            background-color: #1a1d24 !important;
        }
        
        [data-testid="stPopover"] button {
            font-size: 20px !important;
            padding: 8px 12px !important;
        }
        
        /* Style the popover content */
        div[data-baseweb="popover"] {
            background-color: #1a1d24 !important;
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
    
    # Top bar with reviewer name
    col_title, col_spacer, col_user = st.columns([3, 1, 2])
    with col_title:
        st.markdown(f'<p class="main-title">Human review - {len(pending)} remaining</p>', unsafe_allow_html=True)
    with col_spacer:
        st.markdown(f'<p style="text-align: center; color: #666; font-size: 12px; margin-top: 10px;">Item {1} of {len(pending)}</p>', unsafe_allow_html=True)
    with col_user:
        # Initialize reviewer name if not set
        if 'reviewer_name' not in st.session_state:
            st.session_state.reviewer_name = "anonymous"
        
        st.markdown('<p style="color: #888; font-size: 11px; margin-bottom: 2px; margin-top: 5px;">Reviewer</p>', unsafe_allow_html=True)
        reviewer_name = st.text_input(
            "Reviewer", 
            value=st.session_state.reviewer_name,
            key="reviewer_input",
            label_visibility="collapsed",
            placeholder="Enter your name..."
        )
        if reviewer_name:
            st.session_state.reviewer_name = reviewer_name
    
    st.markdown("---")
    
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
                
                # Additional metadata for tracking
                "organization_name": current_review.get('organization_name'),
                "agency_user": current_review.get('agency_user'),
                "user_id": current_review.get('user_id'),
                
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
    
    # Detect duplicate reviews (same item reviewed by multiple people)
    duplicate_reviews = {}
    if 'review_id' in df.columns:
        review_counts = df['review_id'].value_counts()
        duplicates = review_counts[review_counts > 1]
        if len(duplicates) > 0:
            for review_id in duplicates.index:
                reviewers = df[df['review_id'] == review_id]['reviewer'].tolist()
                duplicate_reviews[review_id] = reviewers
    
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
    
    # Show duplicate reviews if any
    if duplicate_reviews:
        st.markdown("---")
        st.markdown("### 🔄 Multiple Reviews (Same Item)")
        st.info(f"📊 {len(duplicate_reviews)} items have been reviewed by multiple people")
        
        with st.expander(f"View {len(duplicate_reviews)} items with multiple reviews"):
            for review_id, reviewers in duplicate_reviews.items():
                # Get the item details
                item_reviews = df[df['review_id'] == review_id]
                if len(item_reviews) > 0:
                    first_review = item_reviews.iloc[0]
                    prompt = first_review.get('prompt', 'Unknown')
                    prompt_display = prompt[:80] + "..." if len(str(prompt)) > 80 else prompt
                    
                    st.markdown(f"**Item:** {prompt_display}")
                    st.markdown(f"**Reviewed by:** {', '.join(set(reviewers))} ({len(reviewers)} reviews)")
                    
                    # Show agreement stats
                    acceptable_votes = item_reviews['acceptable'].sum() if 'acceptable' in item_reviews.columns else 0
                    agreement = f"{acceptable_votes}/{len(item_reviews)} found acceptable"
                    st.caption(f"Agreement: {agreement}")
                    st.markdown("---")
    
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
        
        # Get reviewer name
        reviewer = row.get('reviewer', 'anonymous')
        
        table_data.append({
            'project_title': prompt,
            'timestamp': timestamp,
            'acceptable': acceptable,
            'reviewer': reviewer,
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
            "reviewer": st.column_config.TextColumn(
                "Reviewer",
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


if __name__ == '__main__':
    # Ensure directories exist
    Path("review_data").mkdir(exist_ok=True)
    
    main()

