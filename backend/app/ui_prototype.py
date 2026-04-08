from __future__ import annotations

import streamlit as st

from licensing_assistant import handle_licensing_prompt


st.set_page_config(page_title="Licensing Assistant Prototype", layout="centered")

st.title("RI Licensing Assistant")
st.caption("Prototype: guardrails + licensing retrieval + grounded answer")

query = st.text_area(
    "Ask a Rhode Island licensing question",
    placeholder="Example: How do I apply for a Tiverton business license?",
    height=120,
)

k = st.slider("Number of sources (k)", min_value=1, max_value=8, value=3)

if st.button("Submit", type="primary"):
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Evaluating with guardrails and searching licensing docs..."):
            result = handle_licensing_prompt(query.strip(), k=k)

        decision = result.get("decision", "ALERT")

        if decision == "ALLOW":
            st.success(f"Decision: {decision}")
        elif decision == "ALERT":
            st.warning(f"Decision: {decision}")
        else:
            st.error(f"Decision: {decision}")

        user_message = result.get("user_message")
        answer = result.get("answer")

        if answer:
            st.subheader("Answer")
            st.write(answer)
        elif user_message:
            st.subheader("Message")
            st.write(user_message)

        guardrail = result.get("guardrail", {})
        with st.expander("Guardrail Details"):
            st.json(
                {
                    "severity": guardrail.get("severity"),
                    "final_decision": guardrail.get("final_decision"),
                    "llm_decision": guardrail.get("llm_decision"),
                    "llm_reason": guardrail.get("llm_reason"),
                    "reasons": guardrail.get("reasons", []),
                    "detected": guardrail.get("detected", {}),
                }
            )

        retrieval = result.get("retrieval", [])
        if retrieval:
            st.subheader("Retrieved Sources")
            for idx, chunk in enumerate(retrieval, start=1):
                title = f"#{idx} {chunk.get('file_name')} p.{chunk.get('page_number')} (score={chunk.get('score'):.4f})"
                with st.expander(title):
                    st.write(chunk.get("text", ""))