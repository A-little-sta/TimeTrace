<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { api } from '../services/api';
import { Photo } from '../types';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../store';

const photos = ref<Photo[]>([]);
const isUploading = ref(false);
const dragActive = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const router = useRouter();
const authStore = useAuthStore();

const loadPhotos = async () => {
  try {
    const data = await api.getPhotos();
    photos.value = data;
  } catch (error) {
    console.error("Failed to load photos", error);
  }
};

const processFile = async (file: File) => {
    if (!file.type.match('image.*')) {
        alert("Please upload an image file.");
        return;
    }
    
    isUploading.value = true;
    try {
      const newPhoto = await api.uploadPhoto(file);
      photos.value = [newPhoto, ...photos.value];
    } catch (e) {
      alert("Upload failed: " + (e as Error).message);
    } finally {
      isUploading.value = false;
    }
};

const handleFileUpload = (event: Event) => {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file) processFile(file);
};

const handleDrag = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      dragActive.value = true;
    } else if (e.type === "dragleave") {
      dragActive.value = false;
    }
};

const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragActive.value = false;
    if (e.dataTransfer?.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
};

const triggerUpload = () => {
    fileInput.value?.click();
};

const goToRepair = (photo: Photo) => {
    router.push({
        path: '/workshop/dustless',
        query: { photo: photo.url, id: photo.id }
    });
};

const deleteAllPhotos = async () => {
    if (photos.value.length === 0) {
        alert('图库为空');
        return;
    }
    
    if (confirm('确定要删除图库中的所有照片吗？此操作不可恢复。')) {
        try {
            await api.deleteAllPhotos();
            photos.value = [];
            alert('所有照片已删除');
        } catch (error) {
            console.error('删除所有照片失败', error);
            alert('删除失败：' + (error as Error).message);
        }
    }
};

const deletePhoto = async (photoId: number) => {
    if (confirm('确定要删除这张照片吗？此操作不可恢复。')) {
        try {
            await api.deletePhoto(photoId);
            // 从列表中移除删除的照片
            photos.value = photos.value.filter(photo => photo.id !== photoId);
            alert('照片删除成功');
        } catch (error) {
            console.error('删除照片失败', error);
            alert('删除失败：' + (error as Error).message);
        }
    }
};

onMounted(() => {
    // Check if user is authenticated
    if (!authStore.isAuthenticated) {
        router.push('/login');
        return;
    }
    loadPhotos();
});
</script>

<template>
  <div 
    class="p-8 md:p-12 max-w-7xl mx-auto min-h-full flex flex-col animate-fade-in" 
    @dragenter="handleDrag"
    @dragover="handleDrag"
    @dragleave="handleDrag"
    @drop="handleDrop"
  >
    <!-- Header -->
    <div class="mb-12 flex justify-between items-end">
      <div>
        <h1 class="text-4xl font-serif-title font-bold text-gray-900 tracking-tight mb-3">时光图库</h1>
        <p class="text-gray-500 font-light text-lg">珍藏每一刻回忆，让瞬间成为永恒。</p>
      </div>
      <button 
        v-if="photos.length > 0"
        @click="deleteAllPhotos"
        class="px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-xl text-sm font-medium transition-colors shadow-md hover:shadow-lg"
      >
        删除所有照片
      </button>
    </div>

    <!-- Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
      
      <!-- Upload Card -->
      <div 
          @click="triggerUpload"
          :class="[
            'aspect-[4/5] rounded-3xl border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center cursor-pointer group relative overflow-hidden bg-white/50 backdrop-blur-sm',
            dragActive ? 'border-primary-500 bg-primary-50 scale-95' : 'border-gray-200 hover:border-primary-400 hover:bg-white hover:shadow-xl hover:-translate-y-1'
          ]"
      >
         <input 
           ref="fileInput"
           type="file" 
           class="hidden" 
           accept="image/jpeg,image/png,image/gif" 
           @change="handleFileUpload" 
         />
         
         <div :class="[
            'w-16 h-16 rounded-full flex items-center justify-center mb-6 transition-colors duration-300 z-10',
            isUploading ? 'bg-primary-50 text-primary-600' : 'bg-primary-50/50 text-primary-400 group-hover:bg-primary-500 group-hover:text-white'
         ]">
           <div v-if="isUploading">
               <svg class="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                 <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                 <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
               </svg>
           </div>
           <div v-else>
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
           </div>
         </div>
         <span class="text-lg font-medium text-gray-700 group-hover:text-primary-600 transition-colors font-serif-title z-10">
             {{ isUploading ? '上传中...' : '上传新照片' }}
         </span>
         <span class="text-sm text-gray-400 mt-2 font-light z-10">支持 JPG, PNG, GIF</span>
         
         <div class="absolute -bottom-10 -right-10 w-40 h-40 bg-gradient-to-tl from-primary-100 to-transparent rounded-full opacity-0 group-hover:opacity-50 transition-opacity duration-500"></div>
      </div>

      <!-- Photo Cards -->
      <div 
        v-for="(photo, index) in photos" 
        :key="photo.id" 
        class="group relative aspect-[4/5] rounded-3xl overflow-hidden bg-white shadow-sm hover:shadow-[0_20px_40px_-15px_rgba(207,176,123,0.3)] hover:-translate-y-2 transition-all duration-500 animate-fade-in"
        :style="{ animationDelay: `${index * 50}ms` }"
      >
        <img 
          :src="photo.url" 
          :alt="photo.filename" 
          class="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-700 ease-in-out" 
        />
        
        <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-6">
          <p class="text-white font-medium truncate text-lg font-serif-title">{{ photo.filename }}</p>
          <p class="text-white/60 text-xs mb-4">{{ photo.created_at ? new Date(photo.created_at).toLocaleDateString() : 'Unknown Date' }}</p>
          
          <div class="flex flex-col gap-3">
            <button 
              @click="goToRepair(photo)"
              class="w-full bg-primary-400 hover:bg-primary-500 text-white py-3 rounded-xl text-center transition-colors font-medium text-sm tracking-wide shadow-lg shadow-primary-900/20"
            >
              开始修复
            </button>
            <button 
              @click="deletePhoto(photo.id)"
              class="w-full bg-red-500 hover:bg-red-600 text-white py-3 rounded-xl text-center transition-colors font-medium text-sm tracking-wide shadow-lg shadow-red-900/20"
            >
              删除照片
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Drag Overlay -->
    <div v-if="dragActive" class="absolute inset-0 bg-primary-400/10 backdrop-blur-sm border-4 border-primary-400 border-dashed rounded-3xl m-4 z-50 flex items-center justify-center pointer-events-none">
        <div class="bg-white px-8 py-4 rounded-full shadow-xl text-primary-600 font-bold text-xl animate-bounce">
            释放以上传图片或视频
        </div>
    </div>
  </div>
</template>