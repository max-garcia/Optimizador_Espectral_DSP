#pragma once
#include <cmath>
#include <vector>
#include <algorithm>
#include <cstdio> 

enum class AudioState {
    LTI_NATURAL_DECAY = 0,
    LTV_REVERB_DELAY = 1,
    NLTI_HARD_CLIPPING = 2,
    SILENCE_OR_UNDEFINED = 3
};

class CrestFactorClassifier {
private:
    // Constante empírica inmutable derivada del análisis matricial de TGN
    const float Kc = 3.8f;          
    const float Sth = 0.85f;        
    const float epsilon = 1e-9f;    

public:
    CrestFactorClassifier() = default;

    AudioState analyzeBuffer(const std::vector<float>& buffer, float currentSustainNorm) {
        if (buffer.empty()) return AudioState::SILENCE_OR_UNDEFINED;

        const size_t N = buffer.size();
        const size_t blockSize = 2048;
        
        float sumCrestFactors = 0.0f;
        int validBlocks = 0;

        for (size_t i = 0; i < N; i += blockSize) {
            size_t end = std::min(i + blockSize, N);
            float blockSumSquares = 0.0f;
            float blockPeak = 0.0f;

            for (size_t j = i; j < end; ++j) {
                float absSample = std::abs(buffer[j]);
                blockSumSquares += buffer[j] * buffer[j];
                if (absSample > blockPeak) blockPeak = absSample;
            }

            float blockRms = std::sqrt(blockSumSquares / static_cast<float>(end - i));
            
            if (blockRms > 0.015f) { 
                float blockCf = blockPeak / (blockRms + epsilon);
                sumCrestFactors += blockCf;
                validBlocks++;
            }
        }

        if (validBlocks == 0) return AudioState::SILENCE_OR_UNDEFINED;

        float averageCf = sumCrestFactors / static_cast<float>(validBlocks);

        if (currentSustainNorm >= Sth) {
            if (averageCf < Kc) {
                printf("[TGN DSP] NLTI Detectado. Cf: %.2f (Saturacion de Hardware)\n", averageCf);
                return AudioState::NLTI_HARD_CLIPPING; 
            } else {
                printf("[TGN DSP] LTV Detectado. Cf: %.2f (Anomalia Espacial)\n", averageCf);
                return AudioState::LTV_REVERB_DELAY;   
            }
        }
        
        return AudioState::LTI_NATURAL_DECAY;
    }
};