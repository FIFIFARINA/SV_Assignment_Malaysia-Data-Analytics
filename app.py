import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="Malaysia Data Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("Malaysia Data Analytics Dashboard")
st.markdown(
    "Explore population distribution, household income "
    "and school distribution across Malaysia."
)

# --------------------------------------------------
# LOAD DATASETS
# --------------------------------------------------
@st.cache_data
def load_data():
    population = pd.read_csv("population_district.csv")
    income = pd.read_csv("hh_income_district.csv")
    schools = pd.read_csv("schools_district.csv")

    population["date"] = pd.to_datetime(population["date"])
    income["date"] = pd.to_datetime(income["date"])
    schools["date"] = pd.to_datetime(schools["date"])

    return population, income, schools


try:
    population, income, schools = load_data()
except Exception as e:
    st.error(f"Unable to load datasets: {e}")
    st.stop()


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------
def state_filter(data, key):
    states = sorted(data["state"].dropna().unique())
    return st.multiselect(
        "Select state",
        states,
        default=states,
        key=key
    )


# Exclude national and all-district aggregate records
school_data = schools[
    (schools["state"] != "Malaysia") &
    (schools["district"] != "All Districts")
].copy()

# --------------------------------------------------
# DASHBOARD TABS
# --------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "👥 Population Distribution",
    "💰 Household Income",
    "🏫 School Distribution"
])


# ==================================================
# TAB 1: POPULATION DISTRIBUTION
# ==================================================
with tab1:
    st.header("Population Distribution")

    st.write(
        "Explore population patterns by age group, sex and state."
    )

    # Use overall ethnicity to avoid double counting
    pop = population[
        population["ethnicity"].astype(str).str.lower() == "overall"
    ].copy()

    latest_date = pop["date"].max()
    pop = pop[pop["date"] == latest_date]

    selected_sex = st.selectbox(
        "Select sex",
        ["both", "male", "female"],
        key="pop_sex"
    )

    pop_sex = pop[pop["sex"].str.lower() == selected_sex]

    selected_states = state_filter(pop_sex, "pop_states")

    if selected_states:
        pop_sex = pop_sex[pop_sex["state"].isin(selected_states)]

        # Chart 1: Population by age group
        age_summary = (
            pop_sex.groupby("age", as_index=False)["population"]
            .sum()
        )

        age_summary = age_summary[
            age_summary["age"].str.lower() != "overall"
        ]

        age_order = [
            "0-4", "5-9", "10-14", "15-19", "20-24",
            "25-29", "30-34", "35-39", "40-44", "45-49",
            "50-54", "55-59", "60-64", "65-69", "70-74",
            "75-79", "80-84", "85+"
        ]

        age_summary["age"] = pd.Categorical(
            age_summary["age"],
            categories=age_order,
            ordered=True
        )
        age_summary = age_summary.sort_values("age")

        
        # Summary Box: Population Overview
        total_population = age_summary["population"].sum()

        largest_age_group = age_summary.loc[
            age_summary["population"].idxmax(), "age"
        ]

        largest_age_population = age_summary["population"].max()

        total_states = len(selected_states)

        st.subheader("Population Summary")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Population",
            f"{total_population:,.0f}"
        )

        col2.metric(
            "Largest Age Group",
            str(largest_age_group)
        )

        col3.metric(
            "Selected States",
            total_states
        )


        fig1 = px.bar(
            age_summary,
            x="age",
            y="population",
            title="Population Distribution by Age Group",
            labels={
                "age": "Age Group",
                "population": "Population"
            }
        )
        st.plotly_chart(fig1, use_container_width=True)

        # Chart 2: Population by sex
        sex_data = population[
            (population["date"] == latest_date) &
            (population["ethnicity"].astype(str).str.lower() == "overall") &
            (population["sex"].str.lower().isin(["male", "female"])) &
            (population["age"].str.lower() == "overall") &
            (population["state"].isin(selected_states))
        ]

        sex_summary = (
            sex_data.groupby("sex", as_index=False)["population"]
            .sum()
        )

        fig2 = px.bar(
            sex_summary,
            x="sex",
            y="population",
            color="sex",
            title="Population Distribution by Sex",
            labels={
                "sex": "Sex",
                "population": "Population"
            }
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Chart 3: Population heatmap by state and age
        heatmap_data = (
            pop_sex[pop_sex["age"].str.lower() != "overall"]
            .pivot_table(
                index="state",
                columns="age",
                values="population",
                aggfunc="sum"
            )
        )

        heatmap_data = heatmap_data.reindex(
            columns=[a for a in age_order if a in heatmap_data.columns]
        )

        fig3 = px.imshow(
            heatmap_data,
            aspect="auto",
            color_continuous_scale="YlOrRd",
            title="Population Heatmap by State and Age Group",
            labels={
                "x": "Age Group",
                "y": "State",
                "color": "Population"
            }
        )
        st.plotly_chart(fig3, use_container_width=True)

    else:
        st.warning("Please select at least one state.")


# ==================================================
# TAB 2: HOUSEHOLD INCOME
# ==================================================
with tab2:
    st.header("Household Income")

    st.write(
        "Explore average district-level mean and median household income."
    )

    income_years = sorted(income["date"].dt.year.unique())
    selected_year = st.selectbox(
        "Select year",
        income_years,
        index=len(income_years) - 1,
        key="income_year"
    )

    income_states = state_filter(income, "income_states")

    if income_states:
        income_filtered = income[
            income["state"].isin(income_states)
        ].copy()

        income_filtered["year"] = income_filtered["date"].dt.year

        # Average of district-level values (unweighted)
        income_summary = (
            income_filtered.groupby(["state", "year"], as_index=False)
            .agg(
                avg_district_income=("income_mean", "mean"),
                avg_district_median=("income_median", "mean")
            )
        )

        # Chart 4: Average district-level mean income by state
        income_2024 = income_summary[
            income_summary["year"] == selected_year
        ].sort_values("avg_district_income")

        fig4 = px.bar(
            income_2024,
            x="avg_district_income",
            y="state",
            orientation="h",
            title=f"Average District-Level Mean Household Income by State ({selected_year})",
            labels={
                "avg_district_income": "Income (RM)",
                "state": "State"
            }
        )
        st.plotly_chart(fig4, use_container_width=True)

        # Chart 5: Income trend by state
        complete_states = (
            income_summary.groupby("state")["year"]
            .nunique()
        )
        complete_states = complete_states[
            complete_states == len(income_years)
        ].index

        trend_data = income_summary[
            income_summary["state"].isin(complete_states)
        ]

        fig5 = px.line(
            trend_data,
            x="year",
            y="avg_district_income",
            color="state",
            markers=True,
            title="Average District-Level Mean Household Income Trends",
            labels={
                "year": "Year",
                "avg_district_income": "Income (RM)",
                "state": "State"
            }
        )
        st.plotly_chart(fig5, use_container_width=True)

        # Chart 6: Mean and median income comparison
        fig6_data = income_2024.melt(
            id_vars="state",
            value_vars=[
                "avg_district_income",
                "avg_district_median"
            ],
            var_name="Income Type",
            value_name="Income (RM)"
        )

        fig6_data["Income Type"] = fig6_data["Income Type"].map({
            "avg_district_income": "Average District Mean",
            "avg_district_median": "Average District Median"
        })

        fig6 = px.bar(
            fig6_data,
            x="state",
            y="Income (RM)",
            color="Income Type",
            barmode="group",
            title=f"Comparison of Average District Mean and Median Income ({selected_year})"
        )
        st.plotly_chart(fig6, use_container_width=True)

    else:
        st.warning("Please select at least one state.")


# ==================================================
# TAB 3: SCHOOL DISTRIBUTION
# ==================================================
with tab3:
    st.header("School Distribution")

    st.write(
        "Explore the distribution and trends of schools across Malaysia."
    )

    school_states = state_filter(school_data, "school_states")

    if school_states:
        selected_school_data = school_data[
            school_data["state"].isin(school_states)
        ].copy()

        selected_school_data["year"] = (
            selected_school_data["date"].dt.year
        )

        # Chart 7: Schools by education stage and state (2022)
        school_2022 = selected_school_data[
            selected_school_data["year"] == 2022
        ]

        school_state_stage = (
            school_2022.groupby(
                ["state", "stage"], as_index=False
            )["schools"].sum()
        )

        fig7 = px.bar(
            school_state_stage,
            x="state",
            y="schools",
            color="stage",
            barmode="group",
            title="Distribution of Schools by Education Stage and State (2022)",
            labels={
                "state": "State",
                "schools": "Number of Schools",
                "stage": "Education Stage"
            }
        )
        st.plotly_chart(fig7, use_container_width=True)

       
        # Chart 8: Education trend by stage (2018-2022)
        school_trend = selected_school_data[
            selected_school_data["year"].between(2018, 2022)
        ]

        school_trend = (
            school_trend.groupby(
                ["year", "stage"], as_index=False
            )["schools"].sum()
        )

        school_trend["year"] = school_trend["year"].astype(str)

        fig8 = px.line(
            school_trend,
            x="year",
            y="schools",
            color="stage",
            markers=True,
            facet_col="stage",
            facet_col_wrap=1,
            title="Education Trend by Stage in Malaysia (2018–2022)",
            labels={
                "year": "Year",
                "schools": "Number of Schools",
                "stage": "Education Stage"
            }
        )

        fig8.for_each_annotation(
            lambda a: a.update(text=a.text.split("=")[-1].title())
        )

        fig8.update_xaxes(
            type="category",
            title_text=""
        )

        fig8.update_layout(
            height=750,
            margin=dict(b=90)
        )

        fig8.add_annotation(
            x=0.5,
            y=-0.10,
            xref="paper",
            yref="paper",
            text="Year",
            showarrow=False,
            xanchor="center"
        )

        fig8.update_yaxes(
            title_text="Number of Schools",
            matches=None
        )

        fig8.update_layout(height=750)

        st.plotly_chart(fig8, use_container_width=True)


        # Chart 9: Percentage distribution of schools by state (2022)
        state_total = (
            school_2022.groupby("state", as_index=False)["schools"]
            .sum()
        )

        total_schools = state_total["schools"].sum()

        if total_schools > 0:
            state_total["percentage"] = (
                state_total["schools"] / total_schools * 100
            )

            fig9 = px.pie(
                state_total,
                names="state",
                values="schools",
                title="Percentage Distribution of Schools by State (2022)",
                hole=0.35
            )
            fig9.update_traces(
                textposition="inside",
                textinfo="percent"
            )
            st.plotly_chart(fig9, use_container_width=True)
        else:
            st.warning("No school data available for 2022.")

    else:
        st.warning("Please select at least one state.")


# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("---")
st.caption("Malaysia Data Analytics Dashboard | Data Analysis Project") 
