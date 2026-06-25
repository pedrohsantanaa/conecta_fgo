/* ==========================================================================
   CONECTA FGO - Frontend Logic Controller
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // API base URL configuration
    const API_BASE_URL = `${window.location.origin}/api`;
    const HEALTH_URL = `${window.location.origin}/health`;

    // Elements
    const navItems = document.querySelectorAll(".nav-item");
    const tabPanels = document.querySelectorAll(".tab-panel");
    const systemStatusEl = document.getElementById("system-status");
    const toastContainer = document.getElementById("toast-container");

    // 1. Tab Navigation System
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTab = item.getAttribute("data-tab");

            // Deactivate all nav items & panels
            navItems.forEach(nav => nav.classList.remove("active"));
            tabPanels.forEach(panel => panel.classList.remove("active"));

            // Activate target
            item.classList.add("active");
            document.getElementById(targetTab).classList.add("active");
        });
    });

    // 2. Health Monitoring System
    async function checkSystemHealth() {
        try {
            const response = await fetch(HEALTH_URL);
            if (!response.ok) throw new Error("Backend retornou erro.");
            
            const data = await response.json();
            const indicator = systemStatusEl.querySelector(".status-indicator");
            const text = systemStatusEl.querySelector(".status-text");

            indicator.className = "status-indicator"; // Reset classes
            
            if (data.status === "healthy") {
                if (data.mock_mode) {
                    indicator.classList.add("warning");
                    text.innerHTML = `Conectado <strong>(Modo Simulado)</strong>`;
                } else if (data.mtls_configured) {
                    indicator.classList.add("success");
                    text.innerHTML = `Conectado <strong>(BB Integrado - mTLS)</strong>`;
                } else {
                    indicator.classList.add("warning");
                    text.innerHTML = `Conectado <strong>(Sem mTLS)</strong>`;
                }
            } else {
                indicator.classList.add("error");
                text.textContent = "Backend Instável";
            }
        } catch (error) {
            const indicator = systemStatusEl.querySelector(".status-indicator");
            const text = systemStatusEl.querySelector(".status-text");
            indicator.className = "status-indicator error";
            text.textContent = "Backend Offline";
        }
    }

    // Run health check initially and then every 15 seconds
    checkSystemHealth();
    setInterval(checkSystemHealth, 15000);

    // 3. Custom Toast Notification System
    function showToast(message, type = "info", duration = 5000) {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        
        let icon = "ℹ️";
        if (type === "success") icon = "✅";
        if (type === "error") icon = "❌";
        
        toast.innerHTML = `
            <span class="toast-icon">${icon}</span>
            <span class="toast-message">${message}</span>
        `;
        
        toastContainer.appendChild(toast);
        
        // Remove toast after animation and duration
        setTimeout(() => {
            toast.style.animation = "fadeIn 0.3s reverse forwards";
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, duration);
    }

    // Helper: Formatter for Currency
    function formatCurrency(value) {
        if (value === undefined || value === null) return "R$ 0,00";
        return new Intl.NumberFormat("pt-BR", {
            style: "currency",
            currency: "BRL"
        }).format(value);
    }

    // Helper: Get Dates in AAAAMMDD format
    function getFormattedDates() {
        const today = new Date();
        const nextYear = new Date();
        nextYear.setFullYear(today.getFullYear() + 1);

        const format = (date) => {
            const yyyy = date.getFullYear();
            const mm = String(date.getMonth() + 1).padStart(2, "0");
            const dd = String(date.getDate()).padStart(2, "0");
            return parseInt(`${yyyy}${mm}${dd}`);
        };

        return {
            today: format(today),
            nextYear: format(nextYear)
        };
    }

    // 4. Test Data Auto-populator
    const mockDataGenerators = {
        "no-reserve-form": () => {
            const dates = getFormattedDates();
            const randomId = Math.floor(1000 + Math.random() * 9000);
            return {
                codigoAgenteFinanceiro: 123,
                codigoFundoGarantidor: 1,
                numeroAgenciaContratanteOperacao: 4820,
                codigoIdentificadorExternoOperacao: `FGO-${randomId}`,
                codigoIbgeMunicipio: 355030, // São Paulo
                codigoTipoPessoa: 2, // PJ
                codigoIdentificadorSrf: "12345678000199",
                codigoTipoPublicoAlvo: 2,
                valorFaturamentoBrutoAnual: 350000.00,
                numeroCpfQualificadorOperacao: 11122233344,
                valorOperacaoCredito: 75000.00,
                percentualGarantiaOperacaoCredito: 80.00,
                codigoTipoModalidadeCredito: 1,
                codigoTipoFinalidadeCredito: 1,
                codigoTipoFonteRecurso: 11,
                codigoTipoProgramaCredito: 39,
                dataFormalizacaoOperacao: dates.today,
                dataVencimentoOperacao: dates.nextYear,
                codigoTipoCronogramaAmortizacao: 1,
                codigoTipoCondicaoEspecial: 1,
                codigoTipoFormalizacao: 1,
                valorSubsidioCredito: 0.00,
                dataDespachoExternoOperacao: 0,
                valorCondicaoEspecial: ""
            };
        },
        "with-reserve-form": () => {
            const dates = getFormattedDates();
            const randomId = Math.floor(1000 + Math.random() * 9000);
            return {
                codigoAgenteFinanceiro: 123,
                codigoFundoGarantidor: 1,
                numeroAgenciaContratanteOperacao: 4820,
                codigoIdentificadorExternoOperacao: `FGO-${randomId}`,
                codigoIbgeMunicipio: 355030, // São Paulo
                codigoTipoPessoa: 2, // PJ
                codigoIdentificadorSrf: "12345678000199",
                codigoTipoPublicoAlvo: 2,
                valorFaturamentoBrutoAnual: 350000.00,
                numeroCpfQualificadorOperacao: 11122233344,
                valorOperacaoCredito: 95000.00,
                percentualGarantiaOperacaoCredito: 80.00,
                codigoTipoModalidadeCredito: 1,
                codigoTipoFinalidadeCredito: 1,
                codigoTipoFonteRecurso: 11,
                codigoTipoProgramaCredito: 39,
                dataFormalizacaoOperacao: dates.today,
                dataVencimentoOperacao: dates.nextYear,
                codigoTipoCronogramaAmortizacao: 1,
                codigoTipoCondicaoEspecial: 1,
                codigoTipoFormalizacao: 1,
                valorSubsidioCredito: 0.00,
                dataDespachoExternoOperacao: dates.today,
                valorCondicaoEspecial: ""
            };
        }
    };

    document.querySelectorAll(".fill-mock-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            const targetFormId = btn.getAttribute("data-target");
            const form = document.getElementById(targetFormId);
            const generator = mockDataGenerators[targetFormId];
            
            if (form && generator) {
                const data = generator();
                Object.keys(data).forEach(key => {
                    const input = form.querySelector(`[name="${key}"]`);
                    if (input) {
                        input.value = data[key];
                    }
                });
                showToast("Formulário preenchido com dados de simulação!", "success");
            }
        });
    });

    // Helper: Form data to JSON parser
    function parseFormValues(formElement) {
        const formData = new FormData(formElement);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            // Trim whitespace
            value = value.trim();
            
            if (value === "") {
                continue; // Skip optional empty inputs (like valorCondicaoEspecial)
            }
            
            // Check fields list for types
            const numericIntFields = [
                "codigoAgenteFinanceiro", "codigoFundoGarantidor", "numeroAgenciaContratanteOperacao",
                "codigoIbgeMunicipio", "codigoTipoPessoa", "codigoTipoPublicoAlvo", "codigoTipoModalidadeCredito",
                "codigoTipoFinalidadeCredito", "codigoTipoFonteRecurso", "codigoTipoProgramaCredito",
                "dataFormalizacaoOperacao", "dataVencimentoOperacao", "codigoTipoCronogramaAmortizacao",
                "codigoTipoCondicaoEspecial", "dataDespachoExternoOperacao", "codigoTipoFormalizacao",
                "numeroCpfQualificadorOperacao", "Codigo Agente Financeiro", "Codigo Fundo Garantidor",
                "Numero Reserva Pre Validacao"
            ];
            
            const numericFloatFields = [
                "valorFaturamentoBrutoAnual", "valorOperacaoCredito", "percentualGarantiaOperacaoCredito",
                "valorSubsidioCredito", "valorCondicaoEspecial"
            ];

            if (numericIntFields.includes(key)) {
                data[key] = parseInt(value, 10);
            } else if (numericFloatFields.includes(key)) {
                data[key] = parseFloat(value);
            } else {
                data[key] = value;
            }
        }
        
        return data;
    }

    // Helper: Toggle Form Button Loading state
    function setSubmittingState(formId, isSubmitting) {
        const form = document.getElementById(formId);
        const submitBtn = form.querySelector('button[type="submit"]');
        const btnText = submitBtn.querySelector(".btn-text");
        const spinner = submitBtn.querySelector(".spinner");
        
        if (isSubmitting) {
            submitBtn.disabled = true;
            spinner.classList.remove("hidden");
            // Disable all fields
            form.querySelectorAll("input, select").forEach(el => el.disabled = true);
        } else {
            submitBtn.disabled = false;
            spinner.classList.add("hidden");
            form.querySelectorAll("input, select").forEach(el => el.disabled = false);
        }
    }

    // 5. Submit Handler: Pré-validação sem Reserva
    const noReserveForm = document.getElementById("no-reserve-form");
    const noReserveResultCard = document.getElementById("no-reserve-result");

    noReserveForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        setSubmittingState("no-reserve-form", true);
        noReserveResultCard.classList.add("hidden");

        const payload = parseFormValues(noReserveForm);
        console.log("Payload for Pré-validação sem Reserva:", payload);

        try {
            const response = await fetch(`${API_BASE_URL}/pre-validacoes`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Erro desconhecido na pré-validação.");
            }

            const result = await response.json();
            
            // Populate result cards
            document.getElementById("res-nr-total-financiado").textContent = formatCurrency(result.valorTotalFinanciado);
            document.getElementById("res-nr-margem-disponivel").textContent = formatCurrency(result.valorMargemDisponivelContratacao);

            // Display Results
            noReserveResultCard.classList.remove("hidden");
            noReserveResultCard.scrollIntoView({ behavior: "smooth" });
            showToast("Pré-validação consultada com sucesso!", "success");

        } catch (error) {
            showToast(error.message, "error");
        } finally {
            setSubmittingState("no-reserve-form", false);
        }
    });

    // 6. Submit Handler: Pré-validação com Reserva
    const withReserveForm = document.getElementById("with-reserve-form");
    const withReserveResultCard = document.getElementById("with-reserve-result");

    withReserveForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        setSubmittingState("with-reserve-form", true);
        withReserveResultCard.classList.add("hidden");

        const payload = parseFormValues(withReserveForm);

        try {
            const response = await fetch(`${API_BASE_URL}/pre-validacoes/reservas`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Erro desconhecido na reserva.");
            }

            const result = await response.json();
            
            // Populate result cards
            document.getElementById("res-wr-numero-reserva").textContent = result.numeroReservaPreValidacao || "Reservado";
            document.getElementById("res-wr-total-financiado").textContent = formatCurrency(result.valorTotalFinanciado);
            document.getElementById("res-wr-margem-disponivel").textContent = formatCurrency(result.valorMargemDisponivelContratacao);

            // Populate Cancellation Form fields to make cancellation flow easy to test
            document.getElementById("can-agente").value = payload.codigoAgenteFinanceiro;
            document.getElementById("can-fundo").value = payload.codigoFundoGarantidor;
            document.getElementById("can-reserva").value = result.numeroReservaPreValidacao || "";

            // Display Results
            withReserveResultCard.classList.remove("hidden");
            withReserveResultCard.scrollIntoView({ behavior: "smooth" });
            showToast("Reserva FGO criada com sucesso!", "success");

        } catch (error) {
            showToast(error.message, "error");
        } finally {
            setSubmittingState("with-reserve-form", false);
        }
    });

    // 7. Submit Handler: Cancelamento de Reserva
    const cancelForm = document.getElementById("cancelation-form");
    const cancelResultCard = document.getElementById("cancel-result");

    cancelForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        setSubmittingState("cancelation-form", true);
        cancelResultCard.classList.add("hidden");

        const payload = parseFormValues(cancelForm);

        try {
            const response = await fetch(`${API_BASE_URL}/reservas/cancelamentos`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Erro desconhecido no cancelamento.");
            }

            const result = await response.json();
            
            // Populate result card
            document.getElementById("res-can-status").textContent = result.status;
            document.getElementById("res-can-message").textContent = result.mensagem;

            const badge = document.getElementById("res-can-badge");
            if (result.status === "SUCESSO") {
                badge.className = "badge badge-success";
                badge.textContent = "Sucesso";
            } else {
                badge.className = "badge badge-danger";
                badge.textContent = "Falhou";
            }

            // Display Results
            cancelResultCard.classList.remove("hidden");
            cancelResultCard.scrollIntoView({ behavior: "smooth" });
            showToast("Solicitação de cancelamento concluída!", "success");

        } catch (error) {
            showToast(error.message, "error");
        } finally {
            setSubmittingState("cancelation-form", false);
        }
    });
});
