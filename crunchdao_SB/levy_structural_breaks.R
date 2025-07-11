# ========================================================
# Detecção de Quebras Estruturais com Seções de Lévy
# ========================================================
# Baseado na conversa sobre seções de Lévy e quebras estruturais
# Data: 2025-06-26
# ========================================================

# ========================================================
# Carregar pacotes necessários
# ========================================================
if(!require(ggplot2)){
  install.packages("ggplot2")
  library(ggplot2)
}
if(!require(changepoint)){
  install.packages("changepoint")
  library(changepoint)
}
if(!require(strucchange)){
  install.packages("strucchange")
  library(strucchange)
}
if(!require(quantmod)){
  install.packages("quantmod")
  library(quantmod)
}

# ========================================================
# Função modificada para calcular seções de Lévy
# Agora retorna também as durações e datas de cada seção
# ========================================================
compute_levy_sections_with_durations <- function(log_returns, dates, tau = 0.01, q = 5) {
  n <- length(log_returns)
  
  # Estimar variâncias locais com janelas móveis
  m2 <- rep(NA, n)
  for (i in (q + 1):(n - q)) {
    window <- log_returns[(i - q):(i + q)]
    m2[i] <- var(window)
  }
  
  # Eliminar bordas
  m2 <- m2[(q + 1):(n - q)]
  y <- log_returns[(q + 1):(n - q)]
  dates_adj <- dates[(q + 1):(n - q)]
  N <- length(y)
  
  # Construir seções de Lévy
  sections <- list()
  durations <- c()      # delta_tau - duração de cada seção
  start_dates <- c()    # data de início de cada seção
  end_dates <- c()      # data de fim de cada seção
  
  i <- 1
  while (i <= N) {
    acc_var <- 0
    j <- i
    while (j <= N && acc_var + m2[j] <= tau) {
      acc_var <- acc_var + m2[j]
      j <- j + 1
    }
    if (j > i) {
      S_tau <- sum(y[i:(j - 1)])
      sections[[length(sections) + 1]] <- S_tau
      
      # Duração da seção (delta_tau)
      duration <- j - i
      durations <- c(durations, duration)
      
      # Datas de início e fim
      start_dates <- c(start_dates, as.character(dates_adj[i]))
      end_dates <- c(end_dates, as.character(dates_adj[j - 1]))
      
      i <- j
    } else {
      i <- i + 1
    }
  }
  
  return(list(
    S_tau = unlist(sections),
    durations = durations,
    start_dates = as.Date(start_dates),
    end_dates = as.Date(end_dates)
  ))
}

# ========================================================
# Função para detectar quebras estruturais nas durações
# ========================================================
detect_structural_breaks <- function(durations, dates) {
  # Criar série temporal das durações
  ts_durations <- ts(durations)
  
  # Método 1: changepoint package (PELT algorithm)
  cpt_mean <- cpt.mean(ts_durations, method = "PELT", penalty = "BIC")
  breaks_pelt <- cpts(cpt_mean)
  
  # Método 2: strucchange package (teste de Chow)
  # Criar dataframe para análise
  df_breaks <- data.frame(
    duration = durations,
    index = 1:length(durations)
  )
  
  # Teste de quebra estrutural
  fs_test <- Fstats(duration ~ 1, data = df_breaks)
  breaks_chow <- breakpoints(fs_test)
  
  # Método 3: CUSUM (Cumulative Sum)
  mean_dur <- mean(durations)
  cusum <- cumsum(durations - mean_dur)
  
  return(list(
    pelt_breaks = breaks_pelt,
    chow_breaks = breaks_chow,
    cusum = cusum,
    ts_durations = ts_durations
  ))
}

# ========================================================
# Função para visualizar as quebras estruturais
# ========================================================
plot_structural_breaks <- function(res_levy, res_breaks, main_title = "Análise de Quebras Estruturais") {
  # Criar dataframe para visualização
  df_plot <- data.frame(
    section_index = 1:length(res_levy$durations),
    duration = res_levy$durations,
    start_date = res_levy$start_dates
  )
  
  # Gráfico 1: Durações ao longo do tempo
  p1 <- ggplot(df_plot, aes(x = section_index, y = duration)) +
    geom_line(color = "darkblue") +
    geom_point(color = "darkblue", size = 2) +
    labs(title = paste(main_title, "- Durações das Seções"),
         x = "Índice da Seção",
         y = "Duração (dias)") +
    theme_minimal()
  
  # Adicionar linhas verticais para quebras detectadas
  if(length(res_breaks$pelt_breaks) > 0) {
    p1 <- p1 + geom_vline(xintercept = res_breaks$pelt_breaks, 
                          color = "red", linetype = "dashed", size = 1)
  }
  
  # Gráfico 2: CUSUM das durações
  df_cusum <- data.frame(
    section_index = 1:length(res_breaks$cusum),
    cusum = res_breaks$cusum
  )
  
  p2 <- ggplot(df_cusum, aes(x = section_index, y = cusum)) +
    geom_line(color = "darkgreen", size = 1.2) +
    geom_hline(yintercept = 0, color = "gray50", linetype = "dashed") +
    labs(title = "CUSUM das Durações",
         x = "Índice da Seção",
         y = "CUSUM") +
    theme_minimal()
  
  # Gráfico 3: Média móvel das durações
  window_size <- min(10, floor(length(res_levy$durations) / 5))
  ma_durations <- stats::filter(res_levy$durations, rep(1/window_size, window_size), method = "convolution", sides = 2)
  
  df_ma <- data.frame(
    section_index = 1:length(ma_durations),
    duration = res_levy$durations,
    ma_duration = as.numeric(ma_durations)
  )
  
  p3 <- ggplot(df_ma, aes(x = section_index)) +
    geom_line(aes(y = duration), color = "gray70", alpha = 0.7) +
    geom_line(aes(y = ma_duration), color = "darkred", size = 1.2, na.rm = TRUE) +
    labs(title = "Durações e Média Móvel",
         x = "Índice da Seção",
         y = "Duração (dias)") +
    theme_minimal()
  
  # Retornar os gráficos
  return(list(p1 = p1, p2 = p2, p3 = p3))
}

# ========================================================
# Função para analisar as quebras e mapear para datas
# ========================================================
analyze_breaks <- function(res_levy, res_breaks) {
  # Extrair índices das quebras
  break_indices <- res_breaks$pelt_breaks
  
  if(length(break_indices) == 0) {
    cat("Nenhuma quebra estrutural significativa foi detectada.\n")
    return(NULL)
  }
  
  # Mapear quebras para datas aproximadas
  break_info <- data.frame(
    break_index = break_indices,
    section_date = res_levy$start_dates[break_indices],
    duration_before = NA,
    duration_after = NA,
    change_ratio = NA
  )
  
  # Calcular mudanças nas durações médias
  for(i in 1:length(break_indices)) {
    idx <- break_indices[i]
    
    # Janela antes e depois da quebra
    window <- min(10, floor(length(res_levy$durations) / 4))
    
    before_start <- max(1, idx - window)
    before_end <- idx - 1
    after_start <- idx
    after_end <- min(length(res_levy$durations), idx + window - 1)
    
    if(before_end >= before_start && after_end > after_start) {
      dur_before <- mean(res_levy$durations[before_start:before_end])
      dur_after <- mean(res_levy$durations[after_start:after_end])
      
      break_info$duration_before[i] <- round(dur_before, 2)
      break_info$duration_after[i] <- round(dur_after, 2)
      break_info$change_ratio[i] <- round(dur_after / dur_before, 3)
    }
  }
  
  return(break_info)
}

# ========================================================
# Exemplo de uso com dados reais
# ========================================================

# Carregar dados do IBOVESPA
cat("Carregando dados do IBOVESPA...\n")
dfbvsp <- as.data.frame(getSymbols('^BVSP', periodicity='daily', from='2018-01-01', to='2025-01-31', auto.assign=FALSE))
dfbvsp <- data.frame(
  dia = as.Date(time(BVSP)),
  ibov = as.numeric(dfbvsp$BVSP.Close)
)
dfbvsp <- na.omit(dfbvsp)

# Calcular log-retornos
log_returns <- diff(log(dfbvsp$ibov))
dates <- dfbvsp$dia[-1]  # Remover primeira data devido ao diff

# Aplicar seções de Lévy com foco nas durações
cat("\nCalculando seções de Lévy...\n")
res_levy <- compute_levy_sections_with_durations(
  log_returns = log_returns,
  dates = dates,
  tau = 0.005,  # Ajustar conforme necessário
  q = 5
)

# Detectar quebras estruturais
cat("Detectando quebras estruturais...\n")
res_breaks <- detect_structural_breaks(res_levy$durations, res_levy$start_dates)

# Análise das quebras
cat("\nAnalisando quebras detectadas...\n")
break_analysis <- analyze_breaks(res_levy, res_breaks)

if(!is.null(break_analysis)) {
  cat("\n=== QUEBRAS ESTRUTURAIS DETECTADAS ===\n")
  print(break_analysis)
  
  # Interpretar resultados
  cat("\nInterpretação:\n")
  for(i in 1:nrow(break_analysis)) {
    if(break_analysis$change_ratio[i] < 0.7) {
      cat(sprintf("- Em %s: Aumento significativo na volatilidade (duração caiu de %.1f para %.1f dias)\n",
                  break_analysis$section_date[i],
                  break_analysis$duration_before[i],
                  break_analysis$duration_after[i]))
    } else if(break_analysis$change_ratio[i] > 1.3) {
      cat(sprintf("- Em %s: Redução significativa na volatilidade (duração subiu de %.1f para %.1f dias)\n",
                  break_analysis$section_date[i],
                  break_analysis$duration_before[i],
                  break_analysis$duration_after[i]))
    }
  }
}

# Visualizar resultados
cat("\nGerando visualizações...\n")
plots <- plot_structural_breaks(res_levy, res_breaks, "IBOVESPA")

# Exibir gráficos
print(plots$p1)
print(plots$p2)
print(plots$p3)

# Estatísticas descritivas
cat("\n=== ESTATÍSTICAS DAS SEÇÕES ===\n")
cat(sprintf("Número total de seções: %d\n", length(res_levy$durations)))
cat(sprintf("Duração média: %.2f dias\n", mean(res_levy$durations)))
cat(sprintf("Duração mediana: %.2f dias\n", median(res_levy$durations)))
cat(sprintf("Desvio padrão: %.2f dias\n", sd(res_levy$durations)))
cat(sprintf("Coeficiente de variação: %.2f\n", sd(res_levy$durations)/mean(res_levy$durations)))