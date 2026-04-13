
import json
import time
import streamlit as st
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import RunLifeCycleState

# Dentro de Databricks Apps, o WorkspaceClient autentica sozinho
# via service principal do app — não precisa passar token.
w = WorkspaceClient()

# Troque pelo ID do seu job
JOB_ID = 1049515650934266

st.set_page_config(page_title="Contador de Dias", page_icon="📅")
st.title("📅 Contador de Dias")
st.caption("Exemplo Streamlit → Databricks Job")

col1, col2 = st.columns(2)
with col1:
    data_inicio = st.date_input("Data início")
with col2:
    data_fim = st.date_input("Data fim")

if st.button("Calcular no Databricks", type="primary"):
    if data_fim < data_inicio:
        st.error("A data fim precisa ser maior ou igual à data início.")
        st.stop()

    # 1. Dispara o job passando as datas como notebook_params
    with st.spinner("Disparando job no Databricks..."):
        run = w.jobs.run_now(
            job_id=JOB_ID,
            notebook_params={
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat(),
            },
        )
        run_id = run.run_id

    st.info(f"Run iniciado: `{run_id}`")

    # 2. Polling — espera o job terminar
    progress = st.progress(0, text="Executando...")
    status_placeholder = st.empty()

    while True:
        run_info = w.jobs.get_run(run_id=run_id)
        state = run_info.state.life_cycle_state
        status_placeholder.write(f"Estado: **{state.value}**")

        if state in (
            RunLifeCycleState.TERMINATED,
            RunLifeCycleState.SKIPPED,
            RunLifeCycleState.INTERNAL_ERROR,
        ):
            break

        progress.progress(50, text=f"Estado: {state.value}")
        time.sleep(2)

    progress.progress(100, text="Concluído")

    # 3. Lê o resultado
    result_state = run_info.state.result_state
    if result_state and result_state.value == "SUCCESS":
        # get_run_output retorna o que foi passado em dbutils.notebook.exit()
        task_run_id = run_info.tasks[0].run_id
        output = w.jobs.get_run_output(run_id=task_run_id)
        resultado = json.loads(output.notebook_output.result)

        st.success(f"✅ Resultado: **{resultado['dias']} dias**")
        st.json(resultado)
    else:
        st.error(f"Job falhou: {result_state}")
        st.write(run_info.state.state_message)
