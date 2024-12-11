import time
from datetime import datetime

import streamlit as st


class DashboardState:
    """Singleton class to store dashboard state"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DashboardState, cls).__new__(cls)
            cls._instance.metrics = {
                "total_queries": 0,
                "articles_generated": 0,
                "last_update": None,
                "agent_status": {},
            }
        return cls._instance


def main():
    st.title("News Swarm Dashboard")

    # Get dashboard state
    dashboard = DashboardState()

    # Sidebar metrics
    st.sidebar.header("System Status")
    st.sidebar.metric("Total Queries", dashboard.metrics["total_queries"])
    st.sidebar.metric("Articles Generated", dashboard.metrics["articles_generated"])

    # Main content area
    col1, col2, col3 = st.columns(3)

    # Agent status cards
    for agent_name, status in dashboard.metrics["agent_status"].items():
        with col1:
            st.card(
                title=agent_name,
                text=f"Status: {status.get('status', 'Unknown')}\n"
                f"Last Update: {status.get('last_update', 'Never')}",
            )

    # Auto-refresh every 5 seconds
    time.sleep(5)
    st.rerun()


if __name__ == "__main__":
    main()
