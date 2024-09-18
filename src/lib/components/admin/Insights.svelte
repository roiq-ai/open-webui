<script lang="ts">

    import {toast} from 'svelte-sonner';
    import {onMount, getContext} from 'svelte';
    import Chart from 'chart.js/auto';

    const i18n = getContext('i18n');
    import {getDAU} from "$lib/apis/users";
    import {data} from "autoprefixer";


    let chartCanvas;


    onMount(async () => {
        let stats = [];
        let labels = [];
        const ctx = chartCanvas.getContext('2d');
        const res = await getDAU(
            localStorage.token,
        ).catch((error) => {
            toast.error(error);
        });

        if (res) {
            res.forEach((record) => {
                labels.push(record.last_active_at);
                stats.push(record.email);
            });
            loading = false;

        } else {
            loading = false;
        }
        console.log(labels)
        chart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "DAU",
                        data: stats,
                        borderWidth: 1,
                    },
                ],
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                    },
                },
            },
        });
    });
</script>
<div class="card bg-gradient-info">
    <canvas bind:this={chartCanvas} height="100" id="myChart" width="400"/>
</div>

<style>
</style>

