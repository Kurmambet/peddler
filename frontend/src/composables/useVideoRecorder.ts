// frontend/src/composables/useVideoRecorder.ts
import { ref } from "vue";

export function useVideoRecorder() {
  const isRecording = ref(false);
  const recordingDuration = ref(0);
  const stream = ref<MediaStream | null>(null);

  let mediaRecorder: MediaRecorder | null = null;
  let chunks: Blob[] = [];
  let timer: number | null = null;

  const startRecording = async () => {
    try {
      // Запрашиваем квадратное видео
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: {
          width: { ideal: 400 },
          height: { ideal: 400 },
          aspectRatio: { ideal: 1 },
          facingMode: "user", // Фронталка по умолчанию
        },
      });

      stream.value = mediaStream;
      chunks = [];

      // Находим лучший кодек
      const mimeType = MediaRecorder.isTypeSupported(
        "video/webm;codecs=vp8,opus"
      )
        ? "video/webm;codecs=vp8,opus"
        : "video/webm";

      mediaRecorder = new MediaRecorder(mediaStream, { mimeType });

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      mediaRecorder.start();
      isRecording.value = true;

      const startTime = Date.now();
      timer = window.setInterval(() => {
        recordingDuration.value = Math.floor((Date.now() - startTime) / 1000);
      }, 1000);
    } catch (err) {
      console.error("Camera access denied", err);
      throw err;
    }
  };

  const stopRecording = (): Promise<{ blob: Blob; duration: number }> => {
    return new Promise((resolve) => {
      if (!mediaRecorder) return;

      mediaRecorder.onstop = () => {
        const finalBlob = new Blob(chunks, { type: mediaRecorder?.mimeType });
        const finalDuration = recordingDuration.value;

        // Останавливаем все треки камеры
        stream.value?.getTracks().forEach((t) => t.stop());
        stream.value = null;

        isRecording.value = false;
        recordingDuration.value = 0;
        if (timer) clearInterval(timer);

        resolve({ blob: finalBlob, duration: finalDuration });
      };

      mediaRecorder.stop();
    });
  };

  const cancelRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      stream.value?.getTracks().forEach((t) => t.stop());
      stream.value = null;
      isRecording.value = false;
      recordingDuration.value = 0;
      if (timer) clearInterval(timer);
    }
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
