import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

# Función para cargar dataset classes
@st.cache_data
def load_classes():
    df = pd.read_csv('classes_cleaned.csv')
    df['stat'] = df['stat'].str.title()
    df['description'] = df['description'].apply(lambda x: x if x.endswith('.') else x + '.')
    return df

# Función para cargar dataset weapons
@st.cache_data
def load_weapons():
    df = pd.read_csv('weapons_cleaned.csv')
    return df

# Función para filtrar dataframe por armas recomendadas
def recomendation(selected_class, dictionary, list):
    weapons = load_weapons()
    if selected_class.iloc[0]['name'] != 'Wretch':
        if len(list) != 1:
            if selected_class.iloc[3]['stat_level'] > selected_class.iloc[4]['stat_level']:
                df = weapons.loc[(weapons[dictionary[list[0]]] != 0) & (weapons[dictionary[list[1]]] != 0) & (weapons['strRequired'] > weapons['dexRequired'])].nlargest(2, 'phyAttack')
            elif selected_class.iloc[3]['stat_level'] == selected_class.iloc[4]['stat_level']:
                df = weapons.loc[(weapons[dictionary[list[0]]] != 0) & (weapons[dictionary[list[1]]] != 0)].nlargest(2, 'phyAttack')
            else:
                df = weapons.loc[(weapons[dictionary[list[0]]] != 0) & (weapons[dictionary[list[1]]] != 0) & (weapons['dexRequired'] > weapons['strRequired'])].nlargest(2, 'phyAttack')
        else:
            if selected_class.iloc[3]['stat_level'] > selected_class.iloc[4]['stat_level']:
                df = weapons.loc[(weapons[dictionary[list[0]]] != 0) & (weapons['strRequired'] > weapons['dexRequired'])].nlargest(2, 'phyAttack')
            elif selected_class.iloc[3]['stat_level'] == selected_class.iloc[4]['stat_level']:
                df = weapons.loc[(weapons[dictionary[list[0]]] != 0)].nlargest(2, 'phyAttack')
            else:
                df = weapons.loc[(weapons[dictionary[list[0]]] != 0) & (weapons['dexRequired'] > weapons['strRequired'])].nlargest(2, 'phyAttack')
    else:
        df = weapons.loc[weapons['name'] == 'Serpent-hunter']
    return df

def app():
    # Cargar datasets
    classes_df = load_classes()

    st.title('Analysis of Elden Ring Classes')
    st.subheader('')

    #---SIDEBAR
    st.sidebar.title('Select')

    # Lista de clases para el selectbox
    selectbox_options = list(classes_df['name'].unique())
    selectbox_options.append('Select')
    default_option = selectbox_options.index('Select')

    # Lista de clases para el multiselect
    multiselect_options = list(classes_df['name'].unique())

    # Selectbox
    class_selectbox = st.sidebar.selectbox('Classes', selectbox_options, default_option)

    if class_selectbox != 'Select':

        # Lista de clases filtradas según la clase seleccionada en el selectbox
        filtered_list = [x for x in multiselect_options if x != class_selectbox][:2]
        filtered_list.append(class_selectbox)

        # Multiselect
        class_multiselect = st.sidebar.multiselect('Filter', multiselect_options, default=filtered_list)  # Por defecto se seleccionan las primeras 3 clases

        # Dataframe filtrado según las clases seleccionadas en el multiselect
        filtered_classes_df = classes_df[classes_df['name'].isin(class_multiselect)]

        #---MAIN AREA
        selected_class_df = classes_df.loc[classes_df['name'] == class_selectbox]

        # Mostrar imagen y descripción
        col_image, col_info = st.columns([1, 2])
        with col_image:
            st.image(selected_class_df.iloc[0]['image'], use_container_width=True)
        with col_info:
            st.subheader(selected_class_df.iloc[0]['name'])
            st.write(selected_class_df.iloc[0]['description'])
            st.write('')

            # Mostrar gráfico de barras
            bar_chart = alt.Chart(selected_class_df[['stat', 'stat_level']], title='Stat Levels').mark_bar().encode(
                alt.X('stat_level', title='', scale=alt.Scale(domain=[0, 16])),
                alt.Y('stat', title='', scale=alt.Scale(reverse=True)),
                ).properties(
                    width=450,
                    height=325
                ).configure_mark(
                    opacity=0.5, color='orange')
            st.altair_chart(bar_chart, use_container_width=True)

        st.subheader('Additional Statistics')

        col_metrics, col_radar = st.columns([0.5, 2])
        # Mostrar métricas
        with col_metrics:
            st.write(
                """
                <style>
                [data-testid="stMetricDelta"] svg {
                    display: none;
                }
                </style>
                """,
                unsafe_allow_html=True
                )

            st.metric(label='Level', value=selected_class_df['level'].unique())

            if class_selectbox != 'Wretch':
                min_stats_list = list(selected_class_df.loc[selected_class_df['stat_level'] == selected_class_df['stat_level'].min(),'stat'])
                max_stats_list = list(selected_class_df.loc[selected_class_df['stat_level'] == selected_class_df['stat_level'].max(),'stat'])

                for min_stat in min_stats_list:
                    st.metric(label='Min Stat', value=selected_class_df['stat_level'].min(), delta=min_stat, delta_color='inverse')

                for max_stat in max_stats_list:
                    st.metric(label='Max Stat', value=selected_class_df['stat_level'].max(), delta=max_stat)
            else:
                st.metric(label='Min Stat', value='-', delta='-', delta_color='off')
                st.metric(label='Max Stat', value='-', delta='-', delta_color='off')

        # Mostrar gráfico de radar
        with col_radar:
            radar_chart = px.line_polar(filtered_classes_df, r='stat_level', theta='stat', line_close=True, color='name',
                                        labels={'name':'Classes'},
                                        template='plotly_dark',
                                        title='Classes Comparison'
                                        ).update_traces(
                                            fill='toself'
                                        )
            st.plotly_chart(radar_chart, use_container_width=True)

        stats_dict = {
            'Strength': 'strRequired',
            'Dexterity': 'dexRequired',
            'Intelligence': 'intRequired',
            'Faith': 'faiRequired',
            'Arcane': 'arcRequired'
        }

        best_stats_list = list(selected_class_df.loc[(selected_class_df['stat'] != 'Vigor') & (selected_class_df['stat_level'] == selected_class_df[selected_class_df['stat'] != 'Vigor']['stat_level'].max()), 'stat'])

        weapons_df = recomendation(selected_class_df, stats_dict, best_stats_list)

        st.subheader('Weapon Recommendations')

        # Mostrar recomendaciones
        if class_selectbox != 'Wretch':
            col1, col2, col3, col4 = st.columns([0.9, 1, 0.9, 1])
            col_img1, col_txt1, col_img2, col_txt2 = st.columns([0.9, 1, 0.9, 1])
            with col1:
                st.markdown(f"<p style='text-align: center;'>{weapons_df.iloc[0]['name']}</p>", unsafe_allow_html=True)
                with col_img1:
                    st.image(weapons_df.iloc[0]['image'], use_container_width=True)
                with col_txt1:
                    st.write(f"Category: {weapons_df.iloc[0]['category']}")
                    st.write(f"Weight: {weapons_df.iloc[0]['weight']}")
                    st.write(f"Damage: {weapons_df.iloc[0]['phyAttack']}")
                    for stat in best_stats_list:
                        st.write(f"{stat} required: {weapons_df.iloc[0][stats_dict[stat]]}")
            with col3:
                st.markdown(f"<p style='text-align: center;'>{weapons_df.iloc[1]['name']}</p>", unsafe_allow_html=True)
                with col_img2:
                    st.image(weapons_df.iloc[1]['image'], use_container_width=True)
                with col_txt2:
                    st.write(f"Category: {weapons_df.iloc[1]['category']}")
                    st.write(f"Weight: {weapons_df.iloc[1]['weight']}")
                    st.write(f"Damage: {weapons_df.iloc[1]['phyAttack']}")
                    for stat in best_stats_list:
                        st.write(f"{stat} required: {weapons_df.iloc[1][stats_dict[stat]]}")
        else:
            col1, col2 = st.columns([1.3, 2])
            col_wretch_img, col_wretch_txt = st.columns([1.3, 2])

            with col1:
                st.markdown(f"<p style='text-align: center;'>{weapons_df.iloc[0]['name']}</p>", unsafe_allow_html=True)
                with col_wretch_img:
                    st.image(weapons_df.iloc[0]['image'], use_container_width=True)
                    with col_wretch_txt:
                        st.write(f"Category: {weapons_df.iloc[0]['category']}")
                        st.write(f"Weight: {weapons_df.iloc[0]['weight']}")
                        st.write(f"Damage: {weapons_df.iloc[0]['phyAttack']}")
                        for stat in stats_dict:
                            st.write(f"{stat} required: {weapons_df.iloc[0][stats_dict[stat]]}")

if __name__ == '__main__':
    # Configuración de la página
    st.set_page_config(layout='wide')
    app()

