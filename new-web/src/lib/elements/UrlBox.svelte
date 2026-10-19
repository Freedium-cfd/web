<script lang="ts">
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import config from '@/config';

  let { showProtocol = true }: { showProtocol?: boolean } = $props();
  let url = $state('');
  let altchaPayload = $state<string | null>(null);
  let altchaError = $state<string | null>(null);

  onMount(async () => {
    if (config.ALTCHA_ENABLED) {
      await import('altcha');
    }
  });

  function onAltchaStateChange(event: Event) {
    const detail = (event as CustomEvent<{ state?: string; payload?: string }>).detail;
    if (detail?.state === 'verified' && detail.payload) {
      altchaPayload = detail.payload;
      altchaError = null;
    } else {
      altchaPayload = null;
    }
  }

  async function handleSubmit(event: Event) {
    event.preventDefault();
    const target = url.trim();
    if (!target) return;

    if (!config.ALTCHA_ENABLED) {
      await goto(`/${target}`);
      return;
    }

    if (!altchaPayload) {
      altchaError = 'Please complete the verification.';
      return;
    }

    try {
      const res = await fetch('/altcha/verify', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ payload: altchaPayload }),
      });
      const data = await res.json();
      if (res.ok && data?.ok) {
        await goto(`/${target}`);
      } else {
        altchaPayload = null;
        altchaError = 'Verification failed. Please try again.';
      }
    } catch {
      altchaPayload = null;
      altchaError = 'Verification failed. Please try again.';
    }
  }
</script>

<form class="unlock" class:no-pre={!showProtocol} onsubmit={handleSubmit}>
  {#if showProtocol}
    <div class="pre">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
           stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
      </svg>
      https://
    </div>
  {/if}
  <!-- svelte-ignore a11y_autofocus -->
  <input
    type="text"
    placeholder="paste a link — Medium, NYT, WaPo, Bloomberg, Reuters, Economist, FT, The Athletic, Quora"
    bind:value={url}
    autofocus
    aria-label="Article URL"
  />
  <button type="submit">
    Unlock
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
         stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M5 12h14M13 5l7 7-7 7"/>
    </svg>
  </button>

  {#if config.ALTCHA_ENABLED}
    <div class="altcha-row">
      <altcha-widget challengeurl="/altcha/challenge" onstatechange={onAltchaStateChange}
      ></altcha-widget>
      {#if altchaError}
        <p class="altcha-error" role="alert">{altchaError}</p>
      {/if}
    </div>
  {/if}
</form>

<style>
  .unlock {
    max-width: 760px;
    margin: 0 auto;
    background: var(--bg-2);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 6px;
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: stretch;
    gap: 0;
    transition: border-color 0.15s;
  }
  .unlock:focus-within { border-color: var(--accent-deep); }
  .unlock.no-pre { grid-template-columns: 1fr auto; }

  .pre {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 14px;
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--ink-3);
    border-right: 1px dashed var(--line);
  }
  .pre svg { width: 14px; height: 14px; color: var(--accent); }

  input {
    background: transparent;
    border: none;
    outline: none;
    color: var(--ink);
    font-family: var(--font-sans);
    font-size: 14.5px;
    padding: 14px 16px;
    width: 100%;
  }
  input::placeholder { color: var(--ink-4); }

  button {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    background: var(--accent);
    color: oklch(0.18 0.02 145);
    border: none;
    border-radius: 8px;
    padding: 0 20px;
    font-weight: 600;
    font-size: 13px;
    font-family: var(--font-sans);
    cursor: pointer;
    transition: filter 0.15s;
    white-space: nowrap;
  }
  button:hover { filter: brightness(1.08); }
  button svg { width: 14px; height: 14px; }

  .altcha-row {
    grid-column: 1 / -1;
    padding: 4px 8px 6px;
    --altcha-max-width: 100%;
  }
  .altcha-error {
    margin: 6px 2px 0;
    font-size: 12.5px;
    color: oklch(0.62 0.2 25);
  }

  @media (max-width: 540px) {
    .unlock { grid-template-columns: 1fr auto; }
    .pre { display: none; }
  }
</style>
