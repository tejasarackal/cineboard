import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="CineBoard", page_icon="🎬", layout="wide")
conn = st.connection("snowflake")

# @st.cache_data(ttl=600)
def query_db(sql: str) -> pd.DataFrame:
    df = conn.query(sql, ttl=600)
    df.columns = df.columns.str.lower()
    return df


# Headers
st.header("🎬 CineBoard — TMDB Insights")
st.caption("Genre economics, bankable talent, and trending titles from TMDB.")

# Tabs
tab_trend, tab_roi, tab_talent, tab_budget, tab_evo = st.tabs(
    ["📈 Trending", "💰 Genre ROI", "⭐ Bankable Talent", "🎯 Budget → Outcome", "🧬 Genre Evolution"]
)

# Trending Tab
with tab_trend:
    st.subheader("📈 Trending now - popularity over time (top 10 by popularity)")
    df = query_db("""
        select title, snapshot_date, popularity, is_synthetic
        from tesla_analytics_db.cinema.daily_movie_trends
        order by snapshot_date desc
    """)
    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("snapshot_date:T", title="Date"),
            y=alt.Y("popularity:Q", title="Popularity"),
            color=alt.Color("title:N", title="Movie"),
            tooltip=["title", "snapshot_date", "popularity", "is_synthetic"],
        )
        .properties(
            width=800,
            height=420,
        )
        .interactive()
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption("Most history is synthetic. Real captures accrue per pipeline run.")

    # Genre ROI
    with tab_roi:
        st.subheader("Genre ROI over time (revenue ÷ budget)")
        df = query_db("""
            select 
                genre_name, 
                release_year, 
                average_revenue_to_budget_ratio as avg_roi, 
                movie_count
            from tesla_analytics_db.cinema.agg_genre_roi 
            where average_revenue_to_budget_ratio is not null
        """)
        genres = st.multiselect("Genres", sorted(df.genre_name.unique()),
                                default=["Action", "Comedy", "Drama", "Horror"])
        d = df[df.genre_name.isin(genres)]
        st.altair_chart(
            alt.Chart(d)
            .mark_line(point=True)
            .encode(
                x=alt.X("release_year:O", title="Release Year"), 
                y=alt.Y("avg_roi:Q", title="Avg ROI"),
                color=alt.Color("genre_name:N", title="Genre"), 
                tooltip=["genre_name","release_year","avg_roi","movie_count"]
            )
            .properties(height=420)
            .interactive(),
            use_container_width=True
        )

        st.subheader("Genre Profilt Margin over time (profit ÷ budget)")
        df = query_db("""
            select 
                genre_name, 
                release_year, 
                average_profit_margin as avg_profit_margin, 
                movie_count
            from tesla_analytics_db.cinema.agg_genre_roi 
            where average_profit_margin is not null
        """)
        d = df[df.genre_name.isin(genres)]
        st.altair_chart(
            alt.Chart(d)
            .mark_line(point=True)
            .encode(
                x=alt.X("release_year:O", title="Release Year"), 
                y=alt.Y("avg_profit_margin:Q", title="Avg Profit Margin"),
                color=alt.Color("genre_name:N", title="Genre"), 
                tooltip=["genre_name","release_year","avg_profit_margin","movie_count"]
            )
            .properties(height=420)
            .interactive(),
            use_container_width=True
        )

# Bankable Talent Tab
with tab_talent:
    st.subheader("⭐ Bankable Talent (rating vs. box office)")
    df = query_db("""
        select person_name, role_type, movie_count, average_vote_rating, average_revenue
        from tesla_analytics_db.cinema.agg_talented_cast_member
        where average_revenue > 0          
    """)
    roles = st.multiselect("Role", ["actor", "director"], default=["actor", "director"])
    d = df[df.role_type.isin(roles)]

    base = alt.Chart(d)
    bubbles = base.mark_circle(opacity=0.65).encode(
        x=alt.X("average_revenue:Q", title="Avg revenue per film",
                scale=alt.Scale(type="log")),
        y=alt.Y("average_vote_rating:Q", title="Avg weighted rating",
                scale=alt.Scale(zero=False)),
        size=alt.Size("movie_count:Q", title="Films", scale=alt.Scale(range=[40, 500])),
        color=alt.Color("role_type:N", title="Role"),
        tooltip=["person_name", "role_type", "movie_count",
                 "average_vote_rating", "average_revenue"],
    )
    # label only the standouts
    labels = (
        base.transform_window(
            rank="rank()",
            sort=[alt.SortField("average_vote_rating", order="descending")],
        )
        .transform_filter("datum.rank <= 8")
        .mark_text(align="left", dx=7, fontSize=11)
        .encode(x="average_revenue:Q", y="average_vote_rating:Q", text="person_name:N")
    )
    st.altair_chart((bubbles + labels).properties(height=500), use_container_width=True)
    st.caption("Top-right = high rating **and** high box office — the bankable sweet spot. "
               "Bubble size = number of films; quality is the Bayesian weighted rating.")

# Budget → Outcome Tab
with tab_budget:
    st.subheader("🎯 Does Budget buy Revenue (and ratings)?")
    df = query_db("""
        select budget_tier, average_revenue, average_rating, movie_count
        from tesla_analytics_db.cinema.agg_budget_outcomes
        order by budget_tier
    """)
    c1, c2 = st.columns(2)
    c1.altair_chart( 
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("budget_tier:N", title="Budget Tier"),
            y=alt.Y("average_revenue:Q", title="Average Revenue"),
            tooltip=list(df.columns),
            color=alt.Color("budget_tier:N", title="Budget Tier")
        )
        .properties(height=360, title="Average Revenue by Budget Tier")
        .interactive(),
        use_container_width=True
    )
    c2.altair_chart(
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("budget_tier:N", title="Budget Tier"),
            y=alt.Y("average_rating:Q", title="Average Rating", scale=alt.Scale(zero=False)),
            tooltip=list(df.columns),
            color=alt.Color("budget_tier:N", title="Budget Tier")
        )
        .properties(height=360, title="Average Rating by Budget Tier")
        .interactive(),
        use_container_width=True
    )

# Genre Evolution Tab
with tab_evo:
    st.subheader("Genre popularity over release years")
    df = query_db("""
        select genre_name, release_year, avg(average_popularity) as avg_pop
        from tesla_analytics_db.cinema.agg_genre_evolution 
        group by genre_name, release_year
    """)
    st.altair_chart(
        alt.Chart(df)
        .mark_area(opacity=0.6)
        .encode(
            x=alt.X("release_year:O", title="Release Year"),
            y=alt.Y("avg_pop:Q", title="Average Popularity"),
            color=alt.Color("genre_name:N", title="Genre"),
            tooltip=["genre_name","release_year","avg_pop"]
        )
        .properties(height=420)
        .interactive(),
        use_container_width=True
    )