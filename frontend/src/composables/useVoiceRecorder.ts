// frontend\src\composables\useVoiceRecorder.ts
import { ref } from "vue";

export function useVoiceRecorder() {
  const isRecording = ref(false);
  const recordingDuration = ref(0);
  const audioBlob = ref<Blob | null>(null);

  let mediaRecorder: MediaRecorder | null = null;
  let audioChunks: Blob[] = [];
  let startTime: number = 0;
  let timerInterval: number | null = null;

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // const types = [
      //   "audio/webm;codecs=opus",
      //   "audio/webm",
      //   "audio/ogg;codecs=opus",
      //   "audio/mp4",
      // ];

      // Проверяем поддержку Opus
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      // const mimeType = types.find((type) => MediaRecorder.isTypeSupported(type)) || "";
      // const mimeType = "audio/webm";
      mediaRecorder = new MediaRecorder(stream, { mimeType });
      audioChunks = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        audioBlob.value = new Blob(audioChunks, { type: mimeType });
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      isRecording.value = true;
      startTime = Date.now();

      // Таймер длительности
      timerInterval = window.setInterval(() => {
        recordingDuration.value = Math.floor((Date.now() - startTime) / 1000);
      }, 100);
    } catch (err) {
      console.error("Microphone access denied:", err);
      throw new Error("Microphone access required");
    }
  };

  const stopRecording = async (): Promise<Blob> => {
    return new Promise((resolve) => {
      if (!mediaRecorder || !isRecording.value) {
        throw new Error("Not recording");
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunks, { type: mediaRecorder!.mimeType });
        audioBlob.value = blob;
        isRecording.value = false;

        if (timerInterval) {
          clearInterval(timerInterval);
          timerInterval = null;
        }

        const stream = mediaRecorder!.stream;
        stream.getTracks().forEach((track) => track.stop());

        resolve(blob);
      };

      mediaRecorder.stop();
    });
  };

  const cancelRecording = () => {
    if (mediaRecorder && isRecording.value) {
      mediaRecorder.stop();
      isRecording.value = false;
      recordingDuration.value = 0;
      audioBlob.value = null;

      if (timerInterval) {
        clearInterval(timerInterval);
      }
    }
  };

  return {
    isRecording,
    recordingDuration,
    audioBlob,
    startRecording,
    stopRecording,
    cancelRecording,
  };
}
