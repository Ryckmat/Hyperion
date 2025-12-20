#!/usr/bin/env python3
"""Script pour afficher les specs complètes du PC."""

import platform
import subprocess
import os
from pathlib import Path


def run_command(cmd):
    """Execute une commande et retourne le résultat."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Erreur: {e}"


def get_cpu_info():
    """Informations CPU."""
    print("🖥️  CPU")
    print("=" * 60)
    
    # Modèle CPU
    cpu_model = run_command("lscpu | grep 'Model name' | cut -d ':' -f2 | xargs")
    print(f"   Modèle      : {cpu_model}")
    
    # Nombre de cœurs
    cores = run_command("nproc")
    print(f"   Cœurs       : {cores}")
    
    # Architecture
    arch = platform.machine()
    print(f"   Architecture: {arch}")
    
    # Fréquence
    freq = run_command("lscpu | grep 'MHz' | head -1 | awk '{print $3}'")
    if freq:
        print(f"   Fréquence   : {freq} MHz")
    
    print()


def get_memory_info():
    """Informations RAM."""
    print("💾 RAM")
    print("=" * 60)
    
    # RAM totale
    mem_total = run_command("free -h | grep Mem | awk '{print $2}'")
    print(f"   Total       : {mem_total}")
    
    # RAM utilisée
    mem_used = run_command("free -h | grep Mem | awk '{print $3}'")
    print(f"   Utilisée    : {mem_used}")
    
    # RAM disponible
    mem_available = run_command("free -h | grep Mem | awk '{print $7}'")
    print(f"   Disponible  : {mem_available}")
    
    print()


def get_gpu_info():
    """Informations GPU."""
    print("🎮 GPU")
    print("=" * 60)
    
    # Vérifier si nvidia-smi existe
    nvidia_check = run_command("which nvidia-smi")
    
    if nvidia_check and "nvidia-smi" in nvidia_check:
        # GPU NVIDIA détecté
        gpu_name = run_command("nvidia-smi --query-gpu=name --format=csv,noheader")
        gpu_memory = run_command("nvidia-smi --query-gpu=memory.total --format=csv,noheader")
        gpu_driver = run_command("nvidia-smi --query-gpu=driver_version --format=csv,noheader")
        
        print(f"   Modèle      : {gpu_name}")
        print(f"   VRAM        : {gpu_memory}")
        print(f"   Driver      : {gpu_driver}")
        print(f"   CUDA        : ✅ Disponible")
    else:
        # Pas de GPU NVIDIA, chercher AMD ou Intel
        gpu_info = run_command("lspci | grep -i vga")
        print(f"   Détecté     : {gpu_info}")
        print(f"   CUDA        : ❌ Non disponible")
    
    print()


def get_disk_info():
    """Informations disque."""
    print("💿 DISQUE")
    print("=" * 60)
    
    # Espace total et disponible
    disk_info = run_command("df -h / | tail -1")
    parts = disk_info.split()
    
    if len(parts) >= 4:
        print(f"   Total       : {parts[1]}")
        print(f"   Utilisé     : {parts[2]}")
        print(f"   Disponible  : {parts[3]}")
        print(f"   Utilisation : {parts[4]}")
    
    print()


def get_os_info():
    """Informations système."""
    print("🐧 SYSTÈME")
    print("=" * 60)
    
    # Distribution
    distro = run_command("lsb_release -d | cut -d ':' -f2 | xargs")
    print(f"   Distribution: {distro}")
    
    # Kernel
    kernel = platform.release()
    print(f"   Kernel      : {kernel}")
    
    # Python
    python_version = platform.python_version()
    print(f"   Python      : {python_version}")
    
    print()


def check_ai_capabilities():
    """Vérifie les capacités pour l'IA."""
    print("🤖 CAPACITÉS IA")
    print("=" * 60)
    
    # RAM disponible
    mem_available_gb = run_command("free -g | grep Mem | awk '{print $7}'")
    
    try:
        mem_gb = int(mem_available_gb)
        
        print(f"   RAM dispo   : {mem_gb} GB")
        print()
        print("   Modèles recommandés :")
        
        if mem_gb >= 16:
            print("   ✅ Llama 3.2 (8B)    : Excellente qualité")
            print("   ✅ Qwen 2.5 (7B)     : Très bon en code")
            print("   ✅ Mistral (7B)      : Rapide")
        elif mem_gb >= 8:
            print("   ✅ Llama 3.2 (3B)    : Bonne qualité, léger")
            print("   ✅ Phi-3 Mini (3.8B) : Excellent, optimisé")
            print("   ⚠️  Modèles 7B       : Possible mais lent")
        else:
            print("   ⚠️  RAM insuffisante pour LLM locaux")
            print("   💡 Utiliser API Claude recommandé")
    except:
        print("   ❓ Impossible de déterminer RAM disponible")
    
    print()
    
    # GPU
    nvidia_check = run_command("which nvidia-smi")
    if nvidia_check and "nvidia-smi" in nvidia_check:
        vram = run_command("nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits")
        try:
            vram_gb = int(vram) // 1024
            print(f"   GPU VRAM    : {vram_gb} GB")
            
            if vram_gb >= 8:
                print("   ✅ Inference GPU : Très rapide (recommandé)")
            elif vram_gb >= 4:
                print("   ✅ Inference GPU : Rapide")
            else:
                print("   ⚠️  VRAM limitée  : CPU recommandé")
        except:
            pass
    else:
        print("   ℹ️  Pas de GPU NVIDIA : Inference CPU uniquement")
    
    print()


def main():
    """Affiche toutes les specs."""
    print()
    print("=" * 60)
    print("📊 SPÉCIFICATIONS PC - ANALYSE HYPERION")
    print("=" * 60)
    print()
    
    get_os_info()
    get_cpu_info()
    get_memory_info()
    get_gpu_info()
    get_disk_info()
    check_ai_capabilities()
    
    print("=" * 60)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 60)
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
