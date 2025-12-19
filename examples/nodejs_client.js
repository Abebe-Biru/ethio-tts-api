#!/usr/bin/env node
/**
 * Node.js client example for Oromo TTS API
 * 
 * Install dependencies:
 * npm install axios fs-extra node-fetch
 */

const axios = require('axios');
const fs = require('fs-extra');
const path = require('path');

class OromoTTSClient {
    constructor(apiUrl = 'http://localhost:8001', timeout = 30000) {
        this.apiUrl = apiUrl.replace(/\/$/, '');
        this.timeout = timeout;
        this.client = axios.create({
            baseURL: this.apiUrl,
            timeout: this.timeout,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'OromoTTS-NodeJS-Client/1.0'
            }
        });
    }

    async checkHealth() {
        try {
            const response = await this.client.get('/health');
            return response.data;
        } catch (error) {
            throw new Error(`Health check failed: ${error.message}`);
        }
    }

    async generateSpeech(text, savePath = null) {
        if (!text || !text.trim()) {
            throw new Error('Text cannot be empty');
        }

        try {
            const response = await this.client.post('/tts', 
                { text: text },
                { responseType: 'arraybuffer' }
            );

            const audioBuffer = Buffer.from(response.data);

            if (savePath) {
                await fs.ensureDir(path.dirname(savePath));
                await fs.writeFile(savePath, audioBuffer);
                console.log(`Audio saved to ${savePath}`);
            }

            return audioBuffer;
        } catch (error) {
            throw new Error(`TTS generation failed: ${error.message}`);
        }
    }

    async batchGenerate(texts) {
        if (!texts || texts.length === 0) {
            throw new Error('Texts array cannot be empty');
        }

        try {
            const response = await this.client.post('/batch_tts', 
                { texts: texts },
                { timeout: this.timeout * 2 }
            );
            return response.data;
        } catch (error) {
            throw new Error(`Batch TTS generation failed: ${error.message}`);
        }
    }

    async saveBatchResults(batchResults, outputDir = 'batch_output') {
        await fs.ensureDir(outputDir);
        const savedFiles = [];

        for (let i = 0; i < batchResults.results.length; i++) {
            const result = batchResults.results[i];
            
            // Decode base64 audio
            const audioBuffer = Buffer.from(result.audio_b64, 'base64');
            
            // Save to file
            const filename = `audio_${result.hash.substring(0, 8)}.wav`;
            const filepath = path.join(outputDir, filename);
            
            await fs.writeFile(filepath, audioBuffer);
            savedFiles.push(filepath);
            
            console.log(`Saved batch audio ${i + 1}: ${filepath}`);
        }

        return savedFiles;
    }

    async generateMultipleConcurrent(texts, outputDir = 'concurrent_output') {
        await fs.ensureDir(outputDir);
        
        const generateSingle = async (text, index) => {
            try {
                const filename = `audio_${index.toString().padStart(3, '0')}.wav`;
                const filepath = path.join(outputDir, filename);
                await this.generateSpeech(text, filepath);
                return filepath;
            } catch (error) {
                console.error(`Failed to generate audio for text ${index}: ${error.message}`);
                return null;
            }
        };

        const promises = texts.map((text, index) => generateSingle(text, index));
        const results = await Promise.allSettled(promises);
        
        const successfulResults = results
            .filter(result => result.status === 'fulfilled' && result.value !== null)
            .map(result => result.value);

        console.log(`Generated ${successfulResults.length}/${texts.length} audio files`);
        return successfulResults;
    }
}

// Audio playback utilities (requires additional packages)
async function playAudioWithSox(audioBuffer) {
    // Requires: npm install node-wav speaker
    try {
        const wav = require('node-wav');
        const Speaker = require('speaker');
        
        const result = wav.decode(audioBuffer);
        const speaker = new Speaker({
            channels: result.channelCount,
            bitDepth: result.bitDepth,
            sampleRate: result.sampleRate
        });
        
        speaker.write(result.channelData[0]);
        speaker.end();
        
        return new Promise((resolve) => {
            speaker.on('close', resolve);
        });
    } catch (error) {
        console.warn('Audio playback failed. Install dependencies: npm install node-wav speaker');
        console.warn('Error:', error.message);
    }
}

async function playAudioFile(filepath) {
    // Cross-platform audio playback
    const { spawn } = require('child_process');
    
    let command, args;
    
    switch (process.platform) {
        case 'darwin': // macOS
            command = 'afplay';
            args = [filepath];
            break;
        case 'linux':
            command = 'aplay';
            args = [filepath];
            break;
        case 'win32': // Windows
            command = 'powershell';
            args = ['-c', `(New-Object Media.SoundPlayer '${filepath}').PlaySync()`];
            break;
        default:
            console.warn('Audio playback not supported on this platform');
            return;
    }
    
    return new Promise((resolve, reject) => {
        const player = spawn(command, args);
        
        player.on('close', (code) => {
            if (code === 0) {
                resolve();
            } else {
                reject(new Error(`Audio player exited with code ${code}`));
            }
        });
        
        player.on('error', (error) => {
            console.warn(`Audio playback failed: ${error.message}`);
            resolve(); // Don't fail the whole process
        });
    });
}

// Example functions
async function basicExample() {
    console.log('🧪 Basic TTS Example');
    
    const client = new OromoTTSClient();
    
    try {
        // Check health
        const health = await client.checkHealth();
        console.log('API Status:', health);
        
        if (!health.model_loaded) {
            console.log('❌ Model not loaded. Please wait for the API to initialize.');
            return;
        }
        
        // Generate speech
        const text = "Akkam jirta? Maqaan koo Yaadannoo dha.";
        console.log(`Generating speech for: ${text}`);
        
        const audioBuffer = await client.generateSpeech(text, 'basic_example.wav');
        console.log(`Generated ${audioBuffer.length} bytes of audio`);
        
        // Try to play audio
        await playAudioFile('basic_example.wav');
        
    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

async function batchExample() {
    console.log('\n🧪 Batch TTS Example');
    
    const client = new OromoTTSClient();
    
    try {
        const texts = [
            "Akkam jirta?",
            "Maqaan koo Yaadannoo dha.",
            "Ani Afaan Oromoo nan dubbadha.",
            "Baga nagaan dhuftan!",
            "Otuu nagaan jiraattan."
        ];
        
        console.log(`Generating speech for ${texts.length} texts...`);
        const startTime = Date.now();
        
        const batchResults = await client.batchGenerate(texts);
        const savedFiles = await client.saveBatchResults(batchResults, 'batch_example_output');
        
        const endTime = Date.now();
        console.log(`Batch processing completed in ${(endTime - startTime) / 1000}s`);
        console.log(`Saved ${savedFiles.length} audio files`);
        
    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

async function concurrentExample() {
    console.log('\n🧪 Concurrent TTS Example');
    
    const client = new OromoTTSClient();
    
    try {
        const texts = [
            "Akkam jirta?",
            "Nagaan jirta?",
            "Maqaan koo Yaadannoo dha.",
            "Ani barsiisaa dha."
        ];
        
        console.log(`Generating ${texts.length} speeches concurrently...`);
        const startTime = Date.now();
        
        const savedFiles = await client.generateMultipleConcurrent(texts, 'concurrent_example_output');
        
        const endTime = Date.now();
        console.log(`Concurrent processing completed in ${(endTime - startTime) / 1000}s`);
        console.log(`Generated ${savedFiles.length} audio files`);
        
    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

async function interactiveExample() {
    console.log('\n🧪 Interactive TTS Example');
    console.log("Enter Oromo text (or 'quit' to exit):");
    
    const client = new OromoTTSClient();
    const readline = require('readline');
    
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });
    
    try {
        // Check health first
        const health = await client.checkHealth();
        if (!health.model_loaded) {
            console.log('❌ Model not loaded. Please wait for the API to initialize.');
            rl.close();
            return;
        }
    } catch (error) {
        console.log(`❌ Cannot connect to API: ${error.message}`);
        rl.close();
        return;
    }
    
    const askQuestion = () => {
        rl.question('\n📝 Enter text: ', async (text) => {
            text = text.trim();
            
            if (['quit', 'exit', 'q'].includes(text.toLowerCase())) {
                rl.close();
                return;
            }
            
            if (!text) {
                askQuestion();
                return;
            }
            
            try {
                console.log('🔄 Generating speech...');
                const audioBuffer = await client.generateSpeech(text);
                
                // Save with timestamp
                const timestamp = Date.now();
                const filename = `interactive_${timestamp}.wav`;
                await fs.writeFile(filename, audioBuffer);
                
                console.log(`✅ Audio saved as ${filename}`);
                
                // Try to play
                await playAudioFile(filename);
                
            } catch (error) {
                console.error(`❌ Error: ${error.message}`);
            }
            
            askQuestion();
        });
    };
    
    askQuestion();
    
    rl.on('close', () => {
        console.log('\n👋 Goodbye!');
    });
}

// Performance testing
async function performanceTest() {
    console.log('\n🧪 Performance Test');
    
    const client = new OromoTTSClient();
    
    try {
        const health = await client.checkHealth();
        if (!health.model_loaded) {
            console.log('❌ Model not loaded. Please wait for the API to initialize.');
            return;
        }
        
        const testTexts = [
            "Akkam jirta?",
            "Maqaan koo Yaadannoo dha.",
            "Ani Afaan Oromoo nan dubbadha.",
            "Baga nagaan dhuftan!",
            "Otuu nagaan jiraattan.",
            "Barsiisaan mana barumsaa keessa jira.",
            "Ijoolleen fiigaa taphatanii taphatu.",
            "Addunyaa kana keessatti nagaan haa jiraannu."
        ];
        
        console.log('Testing sequential processing...');
        const sequentialStart = Date.now();
        for (let i = 0; i < testTexts.length; i++) {
            await client.generateSpeech(testTexts[i], `sequential_${i}.wav`);
        }
        const sequentialTime = Date.now() - sequentialStart;
        
        console.log('Testing concurrent processing...');
        const concurrentStart = Date.now();
        await client.generateMultipleConcurrent(testTexts, 'concurrent_test');
        const concurrentTime = Date.now() - concurrentStart;
        
        console.log('Testing batch processing...');
        const batchStart = Date.now();
        const batchResults = await client.batchGenerate(testTexts);
        await client.saveBatchResults(batchResults, 'batch_test');
        const batchTime = Date.now() - batchStart;
        
        console.log('\n📊 Performance Results:');
        console.log(`Sequential: ${sequentialTime}ms`);
        console.log(`Concurrent: ${concurrentTime}ms`);
        console.log(`Batch: ${batchTime}ms`);
        console.log(`Speedup (Concurrent vs Sequential): ${(sequentialTime / concurrentTime).toFixed(2)}x`);
        console.log(`Speedup (Batch vs Sequential): ${(sequentialTime / batchTime).toFixed(2)}x`);
        
    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

// Main execution
async function main() {
    console.log('🎤 Oromo TTS Node.js Client Examples');
    console.log('=' .repeat(50));
    
    try {
        await basicExample();
        await batchExample();
        await concurrentExample();
        
        // Ask if user wants interactive mode
        const readline = require('readline');
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout
        });
        
        rl.question('\n🤔 Run interactive mode? (y/n): ', async (answer) => {
            if (['y', 'yes'].includes(answer.trim().toLowerCase())) {
                rl.close();
                await interactiveExample();
            } else {
                rl.close();
                
                // Ask about performance test
                const rl2 = readline.createInterface({
                    input: process.stdin,
                    output: process.stdout
                });
                
                rl2.question('🚀 Run performance test? (y/n): ', async (answer2) => {
                    if (['y', 'yes'].includes(answer2.trim().toLowerCase())) {
                        await performanceTest();
                    }
                    rl2.close();
                });
            }
        });
        
    } catch (error) {
        console.error('\n❌ Error:', error.message);
        process.exit(1);
    }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('\n👋 Interrupted by user');
    process.exit(0);
});

// Run if called directly
if (require.main === module) {
    main().catch(console.error);
}

module.exports = { OromoTTSClient, playAudioFile };