"""
Script para convertir imágenes a vectores numéricos para entrenamiento

Este script convierte imágenes PNG/JPG a vectores de píxeles normalizados
y genera archivos CSV compatibles con el sistema de entrenamiento distribuido.

Usage:
    python tools/image_to_csv.py --input-dir ./images --output inputs.csv outputs.csv
    python tools/image_to_csv.py --image Fases.png --output inputs.csv outputs.csv
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("ERROR: Se requieren las librerías PIL (Pillow) y numpy")
    print("Instalar con: pip install pillow numpy")
    sys.exit(1)


def image_to_vector(image_path, target_size=(8, 8), grayscale=True):
    """
    Convierte una imagen a un vector numérico normalizado.
    
    Args:
        image_path: Ruta a la imagen
        target_size: Tamaño objetivo (ancho, alto) para redimensionar
        grayscale: Si True, convierte a escala de grises
    
    Returns:
        Lista de floats normalizados [0.0, 1.0]
    """
    try:
        img = Image.open(image_path)
        
        # Convertir a escala de grises si es necesario
        if grayscale and img.mode != 'L':
            img = img.convert('L')
        
        # Redimensionar a tamaño fijo
        img_resized = img.resize(target_size, Image.Resampling.LANCZOS)
        
        # Convertir a array numpy
        img_array = np.array(img_resized, dtype=np.float32)
        
        # Normalizar a [0.0, 1.0]
        img_normalized = img_array / 255.0
        
        # Aplanar a vector 1D
        vector = img_normalized.flatten().tolist()
        
        return vector
    
    except Exception as e:
        print(f"Error procesando {image_path}: {e}")
        return None


def process_directory(input_dir, target_size=(8, 8), grayscale=True):
    """
    Procesa todas las imágenes en un directorio.
    
    Returns:
        Lista de vectores (uno por imagen)
    """
    vectors = []
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
    
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"ERROR: Directorio no existe: {input_dir}")
        return []
    
    image_files = [f for f in input_path.iterdir() 
                   if f.suffix.lower() in image_extensions]
    
    if not image_files:
        print(f"ADVERTENCIA: No se encontraron imágenes en {input_dir}")
        return []
    
    print(f"Procesando {len(image_files)} imágenes...")
    
    for img_file in sorted(image_files):
        print(f"  - {img_file.name}")
        vector = image_to_vector(str(img_file), target_size, grayscale)
        if vector:
            vectors.append(vector)
    
    return vectors


def create_dummy_outputs(num_samples, num_classes=1):
    """
    Crea outputs dummy para demostración.
    En un caso real, estos serían las etiquetas reales de las imágenes.
    
    Args:
        num_samples: Número de muestras
        num_classes: Número de clases de salida (default: 1 para clasificación binaria)
    
    Returns:
        Lista de outputs (etiquetas)
    """
    # Para demostración: asignar etiquetas alternadas
    # En producción, esto vendría de un archivo de etiquetas real
    outputs = []
    for i in range(num_samples):
        # Alternar entre 0 y 1 para clasificación binaria
        label = [float(i % 2)]
        outputs.append(label)
    
    return outputs


def save_csv(data, output_file):
    """Guarda datos como CSV."""
    with open(output_file, 'w') as f:
        for row in data:
            if isinstance(row, list):
                f.write(','.join(str(x) for x in row) + '\n')
            else:
                f.write(str(row) + '\n')
    print(f"✓ Guardado: {output_file} ({len(data)} filas)")


def main():
    parser = argparse.ArgumentParser(
        description='Convierte imágenes a vectores numéricos para entrenamiento'
    )
    parser.add_argument('--input-dir', help='Directorio con imágenes')
    parser.add_argument('--image', help='Imagen individual a procesar')
    parser.add_argument('--output', nargs=2, required=True,
                       metavar=('INPUTS_CSV', 'OUTPUTS_CSV'),
                       help='Archivos CSV de salida (inputs y outputs)')
    parser.add_argument('--size', nargs=2, type=int, default=[8, 8],
                       metavar=('WIDTH', 'HEIGHT'),
                       help='Tamaño objetivo de las imágenes (default: 8x8)')
    parser.add_argument('--color', action='store_true',
                       help='Mantener color (default: escala de grises)')
    
    args = parser.parse_args()
    
    # Determinar modo de entrada
    if args.input_dir:
        vectors = process_directory(args.input_dir, 
                                   target_size=tuple(args.size),
                                   grayscale=not args.color)
    elif args.image:
        print(f"Procesando imagen: {args.image}")
        vector = image_to_vector(args.image,
                                target_size=tuple(args.size),
                                grayscale=not args.color)
        vectors = [vector] if vector else []
    else:
        parser.error("Debe especificar --input-dir o --image")
    
    if not vectors:
        print("ERROR: No se generaron vectores. Verifique las imágenes.")
        sys.exit(1)
    
    # Crear outputs dummy (en producción, estos vendrían de etiquetas reales)
    outputs = create_dummy_outputs(len(vectors))
    
    # Guardar CSV
    inputs_file, outputs_file = args.output
    save_csv(vectors, inputs_file)
    save_csv(outputs, outputs_file)
    
    print(f"\n✓ Conversión completada:")
    print(f"  - {len(vectors)} muestras procesadas")
    print(f"  - Vector de entrada: {len(vectors[0])} características")
    print(f"  - Archivos generados: {inputs_file}, {outputs_file}")
    print(f"\nPara entrenar, ejecuta:")
    print(f"  python -m src.train_client --host 127.0.0.1 --port 9000 train {inputs_file} {outputs_file}")


if __name__ == '__main__':
    main()

