<script lang="ts">

    import { toast } from 'svelte-sonner';
    import { createEventDispatcher } from 'svelte';
    import { onMount, getContext } from 'svelte';
    import { addUser } from '$lib/apis/auths';

    import Modal from '../common/Modal.svelte';
    import { WEBUI_BASE_URL } from '$lib/constants';
    import { Bar } from 'svelte-chartjs';
    import {
        Chart,
        Title,
        Tooltip,
        Legend,
        BarElement,
        CategoryScale,
        LinearScale,
    } from 'chart.js';

    Chart.register(
        Title,
        Tooltip,
        Legend,
        BarElement,
        CategoryScale,
        LinearScale
    );
    import { scaleLinear } from 'd3-scale';

    const i18n = getContext('i18n');
    import {getDAU } from "$lib/apis/users";

    const dispatch = createEventDispatcher();

    export let show = false;

    let loading = false;
    let tab = '';
    let inputRecords = [];

    let width = 500;
    let height = 200;
    let chart;
    let ctx;
    let stats;



    onMount( async () => {
        const res = await getDAU(
            localStorage.token,
        ).catch((error) => {
            toast.error(error);
        });

        if (res) {
            res.forEach((record) => {
                console.log(record)
                inputRecords.push(record);
            });
            loading = false;

        } else {
            loading = false;
        }
        chart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: ['red', 'blue'],
                datasets: [
                    {
                        label: "# of Votes",
                        data: res,
                        backgroundColor: [
                            "rgba(255, 99, 132, 0.2)",
                            "rgba(54, 162, 235, 0.2)",
                            "rgba(255, 206, 86, 0.2)",
                            "rgba(75, 192, 192, 0.2)",
                            "rgba(153, 102, 255, 0.2)",
                            "rgba(255, 159, 64, 0.2)",
                        ],
                        borderColor: [
                            "rgba(255, 99, 132, 1)",
                            "rgba(54, 162, 235, 1)",
                            "rgba(255, 206, 86, 1)",
                            "rgba(75, 192, 192, 1)",
                            "rgba(153, 102, 255, 1)",
                            "rgba(255, 159, 64, 1)",
                        ],
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

<Modal size="sm" bind:show>
    <div class="card bg-gradient-info">
        <canvas id="myChart" width="400" height="100" bind:this={ctx} />
    </div>

</Modal>

<style>
    h2 {
        text-align: center;
    }

    .chart {
        width: 100%;
        max-width: 500px;
        margin: 0 auto;
    }

    svg {
        position: relative;
        width: 100%;
        height: 200px;
    }

    .tick {
        font-family: Helvetica, Arial;
        font-size: 0.725em;
        font-weight: 200;
    }

    .tick line {
        stroke: #e2e2e2;
        stroke-dasharray: 2;
    }

    .tick text {
        fill: #ccc;
        text-anchor: start;
    }

    .tick.tick-0 line {
        stroke-dasharray: 0;
    }

    .x-axis .tick text {
        text-anchor: middle;
    }

    .bars rect {
        fill: #a11;
        stroke: none;
        opacity: 0.65;
    }
</style>

