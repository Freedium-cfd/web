<script lang="ts">
    import { onMount, afterUpdate } from 'svelte';
  
    export let columnWidth = 300; // Default column width
    export let gap = 16; // Gap between items
  
    let container: HTMLElement;
    let items: HTMLElement[];
    let columns: number = 1;
  
    function updateLayout() {
      if (!container) return;
  
      const containerWidth = container.offsetWidth;
      columns = Math.floor(containerWidth / (columnWidth + gap));
      const actualColumnWidth = (containerWidth - (columns - 1) * gap) / columns;
  
      container.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
      container.style.gridGap = `${gap}px`;
  
      items.forEach((item, i) => {
        const column = i % columns;
        const prevItem = items[i - columns];
        const top = prevItem ? prevItem.getBoundingClientRect().bottom + gap : 0;
        
        item.style.gridColumn = `${column + 1}`;
        item.style.gridRow = `${Math.floor(top / 10)}`;
      });
    }
  
    onMount(() => {
      items = Array.from(container.children) as HTMLElement[];
      updateLayout();
      window.addEventListener('resize', updateLayout);
    });
  
    afterUpdate(updateLayout);
  </script>
  
  <div bind:this={container} class="masonry-grid">
    <slot></slot>
  </div>
  
  <style>
    .masonry-grid {
      display: grid;
      width: 100%;
    }
  </style>