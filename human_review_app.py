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

# Import storage backends
from review_storage import ReviewStorage, JSONStorage, CSVStorage

# Initialize storage (can switch to MongoDB later)
STORAGE_TYPE = "json"  # Options: "json", "csv", "mongodb"

if STORAGE_TYPE == "json":
    storage = JSONStorage("review_data/reviews.json")
elif STORAGE_TYPE == "csv":
    storage = CSVStorage("review_data/reviews.csv")
else:
    storage = JSONStorage("review_data/reviews.json")


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
        page_title="LLM Response Review",
        page_icon="📝",
        layout="wide"
    )
    
    st.title("🔍 LLM Response Human Review")
    st.markdown("---")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Select Page",
            ["Review Responses", "View History", "Analytics"]
        )
        
        st.markdown("---")
        st.subheader("Stats")
        
        # Show stats
        all_reviews = storage.get_all_reviews()
        st.metric("Total Reviews", len(all_reviews))
        
        if all_reviews:
            avg_rating = sum(r.get('rating', 0) for r in all_reviews) / len(all_reviews)
            st.metric("Avg Rating", f"{avg_rating:.2f}")
    
    # Main content area
    if page == "Review Responses":
        show_review_page()
    elif page == "View History":
        show_history_page()
    elif page == "Analytics":
        show_analytics_page()


def show_review_page():
    """Main review interface"""
    st.header("Review LLM Responses")
    
    # Load pending reviews
    pending = load_pending_reviews()
    
    if not pending:
        st.info("🎉 No pending reviews! All caught up.")
        
        # Option to view previous reviews
        if st.button("View Review History"):
            st.session_state.page = "View History"
            st.rerun()
        return
    
    # Show progress
    st.progress(0 if not pending else (1 / len(pending)))
    st.caption(f"📊 {len(pending)} responses pending review")
    
    # Get current review
    current_review = pending[0]
    review_id = current_review.get('id', '')
    
    # Layout: Response on left, Review form on right
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📄 LLM Response Details")
        
        # Show metadata
        with st.expander("ℹ️ Metadata", expanded=False):
            st.json({
                "ID": current_review.get('id', 'N/A'),
                "Timestamp": current_review.get('timestamp', 'N/A'),
                "Model": current_review.get('model', 'N/A'),
                "Feature": current_review.get('feature', 'N/A'),
                "User ID": current_review.get('user_id', 'N/A'),
            })
        
        # Display prompt
        st.markdown("### 💬 Prompt")
        st.info(current_review.get('prompt', 'No prompt provided'))
        
        # Display context
        if current_review.get('context'):
            st.markdown("### 📚 Context")
            with st.expander("View Context", expanded=False):
                st.text(current_review.get('context', ''))
        
        # Display response (main focus)
        st.markdown("### 🤖 LLM Response")
        response_text = current_review.get('response', 'No response')
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 4px solid #4CAF50;">
            {response_text}
        </div>
        """, unsafe_allow_html=True)
        
        # Display expected output if available
        if current_review.get('expected_output'):
            st.markdown("### ✅ Expected Output")
            st.success(current_review.get('expected_output'))
    
    with col2:
        st.subheader("📝 Your Review")
        
        # Rating
        rating = st.select_slider(
            "Overall Rating",
            options=[1, 2, 3, 4, 5],
            value=3,
            help="1 = Poor, 5 = Excellent"
        )
        
        # Quick evaluation categories
        st.markdown("#### Evaluation Criteria")
        
        accuracy = st.checkbox("✓ Accurate", value=True)
        relevant = st.checkbox("✓ Relevant", value=True)
        complete = st.checkbox("✓ Complete", value=True)
        well_formatted = st.checkbox("✓ Well Formatted", value=True)
        
        # Issues checkboxes
        st.markdown("#### Issues (if any)")
        
        hallucination = st.checkbox("⚠️ Hallucination/Incorrect Info")
        off_topic = st.checkbox("⚠️ Off Topic")
        incomplete = st.checkbox("⚠️ Incomplete")
        formatting_issue = st.checkbox("⚠️ Formatting Issue")
        other_issue = st.checkbox("⚠️ Other Issue")
        
        # Free-form notes
        notes = st.text_area(
            "Additional Notes",
            placeholder="Add any comments, suggestions, or observations...",
            height=150
        )
        
        # Tags
        tags = st.multiselect(
            "Tags",
            ["excellent", "good", "needs-improvement", "error", "edge-case", "training-data"],
            default=[]
        )
        
        st.markdown("---")
        
        # Action buttons
        col_submit, col_skip = st.columns(2)
        
        with col_submit:
            if st.button("✅ Submit Review", type="primary", use_container_width=True):
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
                    "rating": rating,
                    "criteria": {
                        "accurate": accuracy,
                        "relevant": relevant,
                        "complete": complete,
                        "well_formatted": well_formatted
                    },
                    "issues": {
                        "hallucination": hallucination,
                        "off_topic": off_topic,
                        "incomplete": incomplete,
                        "formatting_issue": formatting_issue,
                        "other": other_issue
                    },
                    "notes": notes,
                    "tags": tags
                }
                
                # Save to storage
                storage.save_review(review_data)
                
                # Mark as reviewed
                mark_as_reviewed(review_id)
                
                st.success("✅ Review saved!")
                st.balloons()
                
                # Move to next
                st.rerun()
        
        with col_skip:
            if st.button("⏭️ Skip", use_container_width=True):
                # Move to end of queue
                pending.append(pending.pop(0))
                pending_file = Path("review_data/pending_reviews.json")
                with open(pending_file, 'w') as f:
                    json.dump(pending, f, indent=2)
                st.rerun()


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

