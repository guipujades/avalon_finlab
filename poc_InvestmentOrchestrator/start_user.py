#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para iniciar o sistema em Modo Usuário
Interface simplificada apenas para consultas
"""

import asyncio
from orchestrator import main

if __name__ == "__main__":
    print("="*70)
    print("INICIANDO SISTEMA MULTI-AGENTE EM MODO USUÁRIO")
    print("="*70)
    print("Interface simplificada para consultas:")
    print("- Perguntas e pesquisas gerais")
    print("- Consulta à base de documentos")
    print("- Respostas processadas pelo pipeline completo")
    print("- Sistema otimizado para uso final")
    print("="*70)
    print()
    
    asyncio.run(main(admin_mode=False)) 