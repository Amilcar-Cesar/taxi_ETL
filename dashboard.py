from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
CSV_PATH = ROOT_DIR / "data" / "yellow_tripdata_2016-03.csv"
PARQUET_PATH = ROOT_DIR / "data" / "output" / "yellow_tripdata_2016-03.parquet"

WEEKDAY_ORDER = [
	"Monday",
	"Tuesday",
	"Wednesday",
	"Thursday",
	"Friday",
	"Saturday",
	"Sunday",
]

PAYMENT_MAP = {
	1: "Credit card",
	2: "Cash",
	3: "No charge",
	4: "Dispute",
}

VENDOR_MAP = {
	1: "Vendor 1",
	2: "Vendor 2",
}

BASE_COLUMNS = [
	"VendorID",
	"tpep_pickup_datetime",
	"tpep_dropoff_datetime",
	"passenger_count",
	"trip_distance",
	"pickup_longitude",
	"pickup_latitude",
	"dropoff_longitude",
	"dropoff_latitude",
	"payment_type",
	"fare_amount",
	"total_amount",
	"tip_amount",
]


def clean_and_enrich(df: pd.DataFrame) -> pd.DataFrame:
	df = df.copy()

	df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"])
	df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"])

	invalid_distance = (df["trip_distance"] <= 0) | (df["trip_distance"] > 100)
	invalid_passengers = (df["passenger_count"] <= 0) | (df["passenger_count"] > 6)
	invalid_fare = df["fare_amount"] < 0
	invalid_duration = df["tpep_pickup_datetime"] > df["tpep_dropoff_datetime"]
	invalid_coordinates = (
		(df["pickup_longitude"] < -74.25559)
		| (df["pickup_longitude"] > -73.70001)
		| (df["pickup_latitude"] < 40.49612)
		| (df["pickup_latitude"] > 40.91553)
		| (df["dropoff_longitude"] < -74.25559)
		| (df["dropoff_longitude"] > -73.70001)
		| (df["dropoff_latitude"] < 40.49612)
		| (df["dropoff_latitude"] > 40.91553)
	)

	valid_mask = ~(
		invalid_distance
		| invalid_passengers
		| invalid_fare
		| invalid_duration
		| invalid_coordinates
	)
	df = df.loc[valid_mask].copy()

	df["duration_min"] = (
		df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
	).dt.total_seconds() / 60

	df["speed_mph"] = df["trip_distance"] * 60 / df["duration_min"]
	df.loc[df["duration_min"] <= 0, "speed_mph"] = pd.NA

	df["revenue_per_mile"] = df["total_amount"] / df["trip_distance"]
	df.loc[df["trip_distance"] <= 0, "revenue_per_mile"] = pd.NA

	df["pickup_hour"] = df["tpep_pickup_datetime"].dt.hour
	df["pickup_date"] = df["tpep_pickup_datetime"].dt.date
	df["pickup_dayofweek"] = df["tpep_pickup_datetime"].dt.day_name()

	df["tip_pct"] = df["tip_amount"] / df["total_amount"] * 100
	df.loc[df["total_amount"] <= 0, "tip_pct"] = pd.NA

	df["vendor_label"] = df["VendorID"].map(VENDOR_MAP).fillna(df["VendorID"].astype(str))
	df["payment_label"] = df["payment_type"].map(PAYMENT_MAP).fillna(df["payment_type"].astype(str))

	return df


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
	if PARQUET_PATH.exists():
		try:
			df = pd.read_parquet(PARQUET_PATH, columns=BASE_COLUMNS)
		except Exception:
			df = pd.read_csv(CSV_PATH, usecols=BASE_COLUMNS)
	else:
		df = pd.read_csv(CSV_PATH, usecols=BASE_COLUMNS)

	df = clean_and_enrich(df)

	PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)
	try:
		df.to_parquet(PARQUET_PATH, index=False)
	except Exception:
		pass

	return df


def build_summaries(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
	summary_by_hour = (
		df.groupby("pickup_hour", as_index=False)
		.agg(
			trips=("pickup_hour", "size"),
			avg_fare=("fare_amount", "mean"),
			avg_total=("total_amount", "mean"),
			avg_tip_pct=("tip_pct", "mean"),
		)
		.sort_values("pickup_hour")
		.round(2)
	)

	summary_by_day = (
		df.groupby("pickup_dayofweek", as_index=False)
		.agg(
			trips=("pickup_dayofweek", "size"),
			avg_fare=("fare_amount", "mean"),
			avg_total=("total_amount", "mean"),
			avg_tip_pct=("tip_pct", "mean"),
		)
		.assign(
			pickup_dayofweek=lambda frame: pd.Categorical(
				frame["pickup_dayofweek"], categories=WEEKDAY_ORDER, ordered=True
			)
		)
		.sort_values("pickup_dayofweek")
		.round(2)
	)

	summary_by_vendor = (
		df.groupby("vendor_label", as_index=False)
		.agg(
			trips=("vendor_label", "size"),
			avg_fare=("fare_amount", "mean"),
			avg_total=("total_amount", "mean"),
			avg_tip_pct=("tip_pct", "mean"),
		)
		.assign(
			vendor_label=lambda frame: pd.Categorical(
				frame["vendor_label"], categories=list(VENDOR_MAP.values()), ordered=True
			)
		)
		.sort_values("vendor_label")
		.round(2)
	)

	summary_by_payment = (
		df.groupby("payment_label", as_index=False)
		.agg(
			trips=("payment_label", "size"),
			avg_fare=("fare_amount", "mean"),
			avg_total=("total_amount", "mean"),
			avg_tip_pct=("tip_pct", "mean"),
		)
		.assign(
			payment_label=lambda frame: pd.Categorical(
				frame["payment_label"], categories=list(PAYMENT_MAP.values()), ordered=True
			)
		)
		.sort_values("payment_label")
		.round(2)
	)

	return {
		"hour": summary_by_hour,
		"day": summary_by_day,
		"vendor": summary_by_vendor,
		"payment": summary_by_payment,
	}


def apply_filters(
	df: pd.DataFrame,
	selected_days: list[str],
	selected_payments: list[str],
	selected_vendors: list[str],
) -> pd.DataFrame:
	mask = (
		df["pickup_dayofweek"].isin(selected_days)
		& df["payment_label"].isin(selected_payments)
		& df["vendor_label"].isin(selected_vendors)
	)
	return df.loc[mask].copy()


def render_summary_table(df: pd.DataFrame, index_column: str) -> None:
	display_df = df.copy()
	display_df[index_column] = display_df[index_column].astype(str)
	display_df = display_df.rename(
		columns={
			index_column: "Categoria",
			"trips": "Viagens",
			"avg_fare": "Tarifa média",
			"avg_total": "Total médio",
			"avg_tip_pct": "Gorjeta média (%)",
		}
	)
	st.dataframe(
		display_df,
		use_container_width=True,
		hide_index=True,
		column_config={
			"Viagens": st.column_config.NumberColumn("Viagens", format="%d"),
			"Tarifa média": st.column_config.NumberColumn("Tarifa média", format="$%.2f"),
			"Total médio": st.column_config.NumberColumn("Total médio", format="$%.2f"),
			"Gorjeta média (%)": st.column_config.NumberColumn("Gorjeta média (%)", format="%.2f%%"),
		},
	)


def main() -> None:
	st.set_page_config(
		page_title="Taxi ETL Dashboard",
		page_icon="🚕",
		layout="wide",
	)

	df = load_data()

	st.title("Dashboard Taxi ETL")
	st.caption(
		"Dashboard criado a partir do sumário do notebook, com filtros de dia da semana, forma de pagamento e fornecedor."
	)

	with st.sidebar:
		st.header("Filtros")
		st.caption("Escolha as dimensões que deseja comparar.")

		selected_days = st.multiselect(
			"Dias da semana",
			options=WEEKDAY_ORDER,
			default=WEEKDAY_ORDER,
		)
		selected_payments = st.multiselect(
			"Forma de pagamento",
			options=list(PAYMENT_MAP.values()),
			default=list(PAYMENT_MAP.values()),
		)
		selected_vendors = st.multiselect(
			"Fornecedores",
			options=list(VENDOR_MAP.values()),
			default=list(VENDOR_MAP.values()),
		)

	if not selected_days or not selected_payments or not selected_vendors:
		st.warning("Selecione pelo menos uma opção em cada filtro para visualizar os gráficos.")
		st.stop()

	filtered_df = apply_filters(df, selected_days, selected_payments, selected_vendors)

	if filtered_df.empty:
		st.warning("Nenhum registro encontrado para a combinação de filtros selecionada.")
		st.stop()

	summaries = build_summaries(filtered_df)

	total_trips = len(filtered_df)
	total_revenue = filtered_df["total_amount"].sum()
	avg_fare = filtered_df["fare_amount"].mean()
	avg_total = filtered_df["total_amount"].mean()
	avg_tip_pct = filtered_df["tip_pct"].mean()

	kpi_left, kpi_mid_left, kpi_mid_right, kpi_right = st.columns(4)
	kpi_left.metric("Viagens filtradas", f"{total_trips:,}")
	kpi_mid_left.metric("Receita total", f"US$ {total_revenue:,.2f}")
	kpi_mid_right.metric("Tarifa média", f"US$ {avg_fare:,.2f}")
	kpi_right.metric("Gorjeta média", f"{avg_tip_pct:,.2f}%")

	st.caption(
		f"Período filtrado: {filtered_df['pickup_date'].min()} até {filtered_df['pickup_date'].max()}"
	)

	tab_overview, tab_hour, tab_day, tab_vendor, tab_payment = st.tabs(
		["Visão geral", "Hora do dia", "Dia da semana", "Fornecedores", "Pagamentos"]
	)

	with tab_overview:
		left, right = st.columns([1.2, 1])
		with left:
			st.subheader("Resumo agregado")
			overview_table = pd.DataFrame(
				{
					"Métrica": ["Viagens", "Receita total", "Tarifa média", "Total médio", "Gorjeta média (%)"],
					"Valor": [
						f"{total_trips:,}",
						f"US$ {total_revenue:,.2f}",
						f"US$ {avg_fare:,.2f}",
						f"US$ {avg_total:,.2f}",
						f"{avg_tip_pct:,.2f}%",
					],
				}
			)
			st.dataframe(overview_table, use_container_width=True, hide_index=True)
		with right:
			st.subheader("Distribuição por hora")
			st.bar_chart(
				summaries["hour"].set_index("pickup_hour")["trips"],
				use_container_width=True,
			)

	with tab_hour:
		st.subheader("Sumário por hora do dia")
		st.bar_chart(
			summaries["hour"].set_index("pickup_hour")["trips"],
			use_container_width=True,
		)
		render_summary_table(summaries["hour"].rename(columns={"pickup_hour": "Hora"}), "Hora")

	with tab_day:
		st.subheader("Sumário por dia da semana")
		st.bar_chart(
			summaries["day"].set_index("pickup_dayofweek")["trips"],
			use_container_width=True,
		)
		render_summary_table(
			summaries["day"].rename(columns={"pickup_dayofweek": "Dia da semana"}),
			"Dia da semana",
		)

	with tab_vendor:
		st.subheader("Sumário por fornecedor")
		st.bar_chart(
			summaries["vendor"].set_index("vendor_label")["trips"],
			use_container_width=True,
		)
		render_summary_table(
			summaries["vendor"].rename(columns={"vendor_label": "Fornecedor"}),
			"Fornecedor",
		)

	with tab_payment:
		st.subheader("Sumário por forma de pagamento")
		st.bar_chart(
			summaries["payment"].set_index("payment_label")["trips"],
			use_container_width=True,
		)
		render_summary_table(
			summaries["payment"].rename(columns={"payment_label": "Forma de pagamento"}),
			"Forma de pagamento",
		)


if __name__ == "__main__":
	main()
