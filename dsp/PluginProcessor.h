#pragma once

#include <vector>
#include "CrestFactorClassifier.h" // Importación del axioma matemático

class PluginProcessor {
private:
    // Instanciación del módulo DSP en memoria estática
    CrestFactorClassifier anomalyDetector;
    
    // Variable de estado temporal retenida entre buffers
    float currentSustainNorm;
    AudioState currentTopologicalState;

    // Subrutina interna para calcular el sustain (simplificada para el ejemplo)
    float calculateEnvelopeSustain(const std::vector<float>& buffer);

public:
    PluginProcessor();
    ~PluginProcessor();

    // Método principal que será invocado constantemente por el Host (DAW/Python)
    // Recibe un puntero al bloque de audio en memoria y su longitud (N)
    void processBlock(const float* channelData, int numSamples);

    // Método para exponer el estado actual a la Interfaz Gráfica
    int getCurrentStateAsInt() const;
};