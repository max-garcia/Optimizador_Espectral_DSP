#include "PluginProcessor.h"

// Inicialización de variables de estado
PluginProcessor::PluginProcessor() : currentSustainNorm(0.0f), currentTopologicalState(AudioState::SILENCE_OR_UNDEFINED) {
}

PluginProcessor::~PluginProcessor() {
}

// Lógica corregida de cálculo de envolvente
float PluginProcessor::calculateEnvelopeSustain(const std::vector<float>& buffer) {
    if (buffer.empty()) return 0.0f;

    // Axioma de Energía Global: Escanear el vector completo, no solo el índice 0.
    float peak = 0.0f;
    for(float sample : buffer) {
        float absSample = std::abs(sample);
        if(absSample > peak) peak = absSample;
    }
    
    // Si la matriz contiene energía significativa, forzamos S_norm a 1.0 
    // para someter la señal a la prueba de saturación (Factor de Cresta).
    if (peak > 0.05f) {
        return 1.0f; 
    }
    return 0.0f;
}

// Bucle de procesamiento discreto de alta prioridad
void PluginProcessor::processBlock(const float* channelData, int numSamples) {
    if (channelData == nullptr || numSamples <= 0) return;

    // 1. Reconstrucción del vector de memoria continua O(N)
    std::vector<float> processBuffer(channelData, channelData + numSamples);

    // 2. Extraer la variable dependiente de la envolvente
    currentSustainNorm = calculateEnvelopeSustain(processBuffer);

    // 3. Ejecutar el modelo matemático para anular el falso positivo LTV
    currentTopologicalState = anomalyDetector.analyzeBuffer(processBuffer, currentSustainNorm);

    // El resultado queda almacenado en currentTopologicalState para ser leído por el Host.
}

// Retorno de estado para la Interfaz de Función Foránea (FFI / Python)
int PluginProcessor::getCurrentStateAsInt() const {
    return static_cast<int>(currentTopologicalState);
}

// [Añadir al final de PluginProcessor.cpp]

// [Reemplazar el bloque extern "C" final en PluginProcessor.cpp]

// 1. Definición de la macro transversal de exportación (Axioma de portabilidad)
#if defined(_WIN32) || defined(_MSC_VER) || defined(__MINGW32__)
    #define TGN_EXPORT __declspec(dllexport)
#else
    #define TGN_EXPORT __attribute__((visibility("default")))
#endif

extern "C" {
    // 2. Instanciación en el Heap: Retorno estricto de Puntero Opaco (void*)
    TGN_EXPORT void* PluginProcessor_Create() {
        // Se reserva la memoria del objeto C++ y se oculta su tipo hacia el exterior
        return static_cast<void*>(new PluginProcessor());
    }

    // 3. Inyección del buffer: Recepción de void* y casteo de retorno a la clase C++
    TGN_EXPORT void PluginProcessor_ProcessBlock(void* processor_ptr, const float* buffer, int length) {
        if (processor_ptr != nullptr && buffer != nullptr) {
            PluginProcessor* processor = static_cast<PluginProcessor*>(processor_ptr);
            processor->processBlock(buffer, length);
        }
    }

    // 4. Extracción de estado topológico
    TGN_EXPORT int PluginProcessor_GetState(void* processor_ptr) {
        if (processor_ptr != nullptr) {
            PluginProcessor* processor = static_cast<PluginProcessor*>(processor_ptr);
            return processor->getCurrentStateAsInt();
        }
        return 3; // Estado axiomático de falla (SILENCE_OR_UNDEFINED)
    }

    // 5. Destrucción explícita de la memoria para prevenir Memory Leaks
    TGN_EXPORT void PluginProcessor_Destroy(void* processor_ptr) {
        if (processor_ptr != nullptr) {
            PluginProcessor* processor = static_cast<PluginProcessor*>(processor_ptr);
            delete processor;
        }
    }
}