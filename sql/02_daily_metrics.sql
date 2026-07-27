with daily_events as (
    select
        event_date,
        count(*) as events,
        count(distinct visitorid) as active_users
    from events
    group by event_date
),
first_views as (
    select
        visitorid,
        cast(view_time as date) as event_date,
        case
            when transaction_time is not null then 1
            else 0
        end as is_buyer
    from user_funnel
)
select
    d.event_date,
    d.events,
    d.active_users,
    count(f.visitorid) as new_users,
    sum(f.is_buyer) as buyers,
    cast(sum(f.is_buyer) as double) / count(f.visitorid) as conversion
from daily_events d
left join first_views f
    on d.event_date = f.event_date
group by
    d.event_date,
    d.events,
    d.active_users
order by d.event_date;
