// frontend/src/composables/useVideoRecorder.ts
import { ref } from "vue";
// @ts-ignore — так как у библиотеки может не быть типов
import fixWebmDuration from "fix-webm-duration";

export function useVideoRecorder() {
  const isRecording = ref(false);
  const recordingDuration = ref(0);
  const stream = ref<MediaStream | null>(null);

  let mediaRecorder: MediaRecorder | null = null;
  let chunks: Blob[] = [];
  let timer: any = null;
  let startTime = 0; // Для точного подсчета времени

  const stopAllTracks = () => {
    if (stream.value) {
      stream.value.getTracks().forEach((track) => {
        track.stop();
        track.enabled = false;
      });
      stream.value = null;
    }
  };

  const startRecording = async () => {
    try {
      stopAllTracks();

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: {
          facingMode: "user",
          frameRate: { ideal: 30 },
          // width/height можно не задавать, Firefox сам подберет
        },
      });

      stream.value = mediaStream;
      chunks = [];

      // Пробуем кодеки. VP8 — самый надежный для кросс-браузерности (Chrome <-> FF)
      const types = [
        "video/webm;codecs=vp8,opus",
        "video/webm;codecs=vp8",
        "video/webm",
      ];
      const mimeType =
        types.find((type) => MediaRecorder.isTypeSupported(type)) || "";

      console.log("[VideoRecorder] Using mimeType:", mimeType);

      mediaRecorder = new MediaRecorder(mediaStream, {
        mimeType,
        videoBitsPerSecond: 1500000,
      });

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      // timeslice 1000мс можно оставить, но для fixWebmDuration
      // важнее всего итоговый Blob всех чанков
      mediaRecorder.start(1000);

      isRecording.value = true;
      startTime = Date.now();

      timer = setInterval(() => {
        // Обновляем UI (секунды)
        recordingDuration.value = Math.floor((Date.now() - startTime) / 1000);
      }, 1000);
    } catch (err) {
      console.error("Camera access error:", err);
      stopAllTracks();
      throw err;
    }
  };

  const stopRecording = (): Promise<{ blob: Blob; duration: number }> => {
    return new Promise((resolve) => {
      if (!mediaRecorder) return;

      mediaRecorder.onstop = () => {
        // 1. Собираем "сырой" Blob
        const rawBlob = new Blob(chunks, { type: mediaRecorder?.mimeType });

        // 2. Вычисляем точную длительность в мс
        const durationMs = Date.now() - startTime;
        const finalDurationSec = Math.floor(durationMs / 1000); // Для UI/БД

        stopAllTracks();
        isRecording.value = false;
        recordingDuration.value = 0;
        if (timer) clearInterval(timer);

        // 3. МАГИЯ: Исправляем заголовки WebM
        fixWebmDuration(rawBlob, durationMs, (fixedBlob: Blob) => {
          // fixedBlob теперь содержит корректный Header с Duration
          resolve({
            blob: fixedBlob,
            duration: finalDurationSec || 1, // Минимум 1 сек, чтобы не ломать логику
          });
        });
      };

      mediaRecorder.stop();
    });
  };

  const cancelRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    stopAllTracks();
    isRecording.value = false;
    recordingDuration.value = 0;
    if (timer) clearInterval(timer);
  };

  return {
    isRecording,
    recordingDuration,
    stream,
    startRecording,
    stopRecording,
    cancelRecording,
  };
}
