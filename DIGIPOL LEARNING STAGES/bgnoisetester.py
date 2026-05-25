import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Reshape
from sklearn.model_selection import train_test_split

def fix_length(y):
    if len(y) > 48000:
        return y[:48000]
    else:
        return np.pad(y, (0, 48000 - len(y)))

def add_noise_at_snr(signal, target_snr_db):
    signal_power = np.mean(signal ** 2)
    noise = np.random.randn(len(signal))
    noise_power = np.mean(noise ** 2)
    scale = np.sqrt(signal_power / (noise_power * 10 ** (target_snr_db / 10)))
    return signal + scale * noise

def chop_into_clips(y, clip_length=48000):
    clips = []
    for i in range(0, len(y), clip_length):
        chunk = y[i:i+clip_length]
        if len(chunk) == clip_length:
            clips.append(chunk)
    return clips

# load audio first
y, sr = librosa.load(r"C:\Users\freddie\Desktop\DIGIPOL LEARNING STAGES\Linkin Park - Faint.mp3", sr=16000)
clips = chop_into_clips(y)
print(len(clips))

# build dataset
X = []
y_labels = []

for clip in clips:
    mfcc_clean = librosa.feature.mfcc(y=clip, sr=sr, n_mfcc=40)
    X.append(mfcc_clean)
    y_labels.append(0)
    
    noisy_clip = add_noise_at_snr(clip, target_snr_db=5)
    mfcc_noisy = librosa.feature.mfcc(y=noisy_clip, sr=sr, n_mfcc=40)
    X.append(mfcc_noisy)
    y_labels.append(1)

X = np.array(X)
y_labels = np.array(y_labels)


# model
cnn_model = Sequential([
    Reshape((40, 94, 1), input_shape=(40, 94)),
    Conv2D(32, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),
    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),
    Flatten(),
    Dense(64, activation='relu'),
    Dense(1, activation='sigmoid')
])

X_train, X_test, y_train, y_test = train_test_split(X, y_labels, test_size=0.2, random_state=42)
cnn_model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
history = cnn_model.fit(X_train, y_train, epochs=10, validation_data=(X_test, y_test))

print("\n--- STRESS TEST ---")
for snr in [20, 10, 5, 0, -5]:
    X_stress = []
    for clip in clips:
        noisy_clip = add_noise_at_snr(clip, target_snr_db=snr)
        mfcc = librosa.feature.mfcc(y=noisy_clip, sr=sr, n_mfcc=40)
        X_stress.append(mfcc)
    X_stress = np.array(X_stress)
    predictions = (cnn_model.predict(X_stress, verbose=0) > 0.5).astype(int)
    accuracy = np.mean(predictions == 1)
    print(f"SNR {snr:4d}dB → {accuracy*100:.1f}% detected as noisy")

snr_levels = [20, 10, 5, 0, -5]
detection_rates = [5.6, 98.1, 100.0, 100.0, 100.0]

plt.plot(snr_levels, detection_rates, marker='o')
plt.xlabel('SNR (dB)')
plt.ylabel('Detection Rate (%)')
plt.title('Stress Test — Noise Detection vs SNR')
plt.gca().invert_xaxis()
plt.grid(True)
plt.show()

cnn_model.summary()
print(len(clips))
print(X.shape)
print(y_labels.shape)