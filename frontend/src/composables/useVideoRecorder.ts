// frontend/src/composables/useVideoRecorder.ts
import { ref } from "vue";

export function useVideoRecorder() {
  const isRecording = ref(false);
  const recordingDuration = ref(0);
  const stream = ref<MediaStream | null>(null);
  let mediaRecorder: MediaRecorder | null = null;
  let chunks: Blob[] = [];
  let timer: any = null;

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
      stopAllTracks(); // Тотальная зачистка перед стартом

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: {
          facingMode: "user",
          // Запрашиваем стандарт, который есть у ЛЮБОЙ камеры
          width: { ideal: 640 },
          height: { ideal: 480 },
        },
      });

      stream.value = mediaStream;
      chunks = [];

      // Явно указываем кодеки, которые Chrome понимает на 100%
      const mimeType = MediaRecorder.isTypeSupported(
        "video/webm;codecs=vp8,opus"
      )
        ? "video/webm;codecs=vp8,opus"
        : "video/webm";

      mediaRecorder = new MediaRecorder(mediaStream, {
        mimeType,
        videoBitsPerSecond: 1200000,
      });

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      // Тайм-слайс 1000мс заставляет Firefox вшивать временные метки (Clusters)
      mediaRecorder.start(1000);
      isRecording.value = true;

      const startTs = Date.now();
      timer = setInterval(() => {
        recordingDuration.value = Math.floor((Date.now() - startTs) / 1000);
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
        const finalBlob = new Blob(chunks, { type: mediaRecorder?.mimeType });
        const finalDuration = recordingDuration.value;
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
      try {
        mediaRecorder.stop();
      } catch (e) {}
    }
    stream.value?.getTracks().forEach((t) => t.stop());
    stream.value = null;
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
