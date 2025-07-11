#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para iniciar o sistema em Modo Administrador
Acesso completo a todas as funcionalidades + conversas com agentes
"""

import asyncio
from orchestrator import main

if __name__ == "__main__":
    print("="*70)
    print("INICIANDO SISTEMA MULTI-AGENTE EM MODO ADMINISTRADOR")
    print("="*70)
    print("Funcionalidades disponíveis:")
    print("- Consultas completas com pipeline multi-agente")
    print("- Conversas diretas com Maestro, Supervisor e Meta-Auditor")
    print("- Comandos de sistema e gerenciamento")
    print("- Configuração de parâmetros")
    print("- Relatórios detalhados e estatísticas")
    print("="*70)
    print()
    
    asyncio.run(main(admin_mode=True)) 